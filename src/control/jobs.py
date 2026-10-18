"""Background jobs run now by a person (owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md A): the jobs app/main.py
declares, registered at start (:func:`register`); Admin runs one of :data:`RUNNABLE` at once, from the Việc nền page or
through the assistant on a Xác nhận (BRD-RULE-ROLE-04: operations are Admin's).

``job_runs``: one row per manual run — running → done or failed, with who asked, when, how long and the record's
summary. One run at a time per job; a row left running ``STALE_S`` (a server that stopped) is failed, so the job can
run again. Each run is audited (``job.run_now``, ``job.run_done``); a run that fails raises the ``job`` alert. The
scheduled runs keep their own records and alerts, as before: this only adds the person's runs.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from control import audit, db, roles
from control.errors import Conflict

STALE_S = 30 * 60
# the fetches and checks a person may want again at once; the clockwork (heartbeat, agent_worker, memory consolidation,
# retention) and the market-history load (its own request, POST /api/market/load) are not run by hand
RUNNABLE = {
    "news_ingest": "Lấy tin",
    "news_reference": "Tin tham chiếu",
    "market_equity": "Thị trường cổ phiếu",
    "market_flows": "Dòng tiền khối ngoại",
    "market_yields": "Lợi suất trái phiếu",
    "market_fx": "Tỷ giá",
    "market_world": "Thị trường thế giới",
    "market_crypto": "Tiền mã hóa",
    "market_gold": "Giá vàng",
    "policy_sweep": "Quét chính sách cho từng gia đình",
    "audit_check": "Kiểm tra chuỗi nhật ký",
    "inbox_import": "Nhập gói từ vùng AI",
    "zone_sync": "Gửi danh mục cho vùng AI",
    "accuracy_score": "Chấm độ chính xác",
}

_JOBS: Dict[str, Any] = {}  # name → operonx Job, from app/main.py
_TASKS: set = set()  # the runs in flight, kept so the loop does not drop them


def register(jobs: List[Any]) -> None:
    for j in jobs:
        _JOBS[j.name] = j


def label(job: str) -> str:
    return RUNNABLE.get(job, job)


def _row(r) -> Dict[str, Any]:
    out = db.load(r)
    out["label"] = label(out["job"])
    return out


def _check(job: str) -> None:
    if job not in RUNNABLE:
        known = ", ".join(f"{k} ({v})" for k, v in RUNNABLE.items())
        raise ValueError(f"Việc {job!r} không chạy tay được. Chạy tay được: {known}")
    if job not in _JOBS:
        raise Conflict(f"Việc {job} chưa được nạp trong tiến trình này")


def running(job: str) -> Optional[Dict[str, Any]]:
    with db.tx() as con:
        r = con.execute(
            "select * from job_runs where job = ? and status = 'running' order by created desc limit 1", (job,)
        ).fetchone()
    return _row(r) if r is not None else None


def start(job: str, by: str) -> Dict[str, Any]:
    """The run recorded as running (or refused): Admin only, a job on the list, one at a time per job."""
    roles.require(by, "admin")
    _check(job)
    now = time.time()
    with db.tx() as con:
        for r in con.execute("select * from job_runs where status = 'running' and created < ?", (now - STALE_S,)):
            _set(con, r, "failed", error="Không xong sau 30 phút (tiến trình chạy đã dừng)", finished=now)
        open_ = con.execute("select * from job_runs where job = ? and status = 'running'", (job,)).fetchone()
        if open_ is not None:
            raise Conflict(f"{label(job)} đang chạy (lần {open_['id']}, {db.load(open_)['by']} bấm); chờ nó xong")
        seq = db.next_seq(con, "job_run")
        rid = f"JR-{seq:06d}"
        con.execute(
            "insert into job_runs values (?, ?, 'running', ?, ?)", (rid, job, now, db.dumps({"by": by, "started": now}))
        )
        audit.append(con, by, "job.run_now", rid, {"job": job})
    return get(rid)


async def execute(run_id: str) -> Dict[str, Any]:
    """Run the job of a started row and record how it went (never raises: a crash is a failed run Admin sees)."""
    r = get(run_id)
    job = _JOBS[r["job"]]
    t0 = time.time()
    try:
        rec = await job.run(trigger={"by": r["by"], "manual": run_id})
        failed = len(rec.failed) + len(rec.timed_out)
        error = "; ".join(f"{k}: {v}" for k, v in list(rec.errors.items())[:3])[:500] if failed else None
        summary = {"items": len(rec.items), "failed": failed, "record": rec.run_id}
    except Exception as exc:  # noqa: BLE001 — recorded as the run's failure
        error, summary = f"{type(exc).__name__}: {exc}"[:500], {}
    return finish(run_id, error, time.time() - t0, summary)


def finish(run_id: str, error: Optional[str], seconds: float, summary: Dict[str, Any]) -> Dict[str, Any]:
    with db.tx() as con:
        r = con.execute("select * from job_runs where id = ?", (run_id,)).fetchone()
        _set(con, r, "failed" if error else "done", error=error, finished=time.time(), seconds=round(seconds, 1),
             summary=summary)  # fmt: skip
        audit.append(con, "system:jobs", "job.run_done", run_id, {"job": r["job"], "error": error})
    if error:
        from control import alerts

        alerts.raise_("job", r["job"], f"{label(r['job'])} chạy tay lỗi ({run_id})", error)
    return get(run_id)


def run_now(job: str, by: str) -> Dict[str, Any]:
    """Started now, in this server's loop; the answer comes back at once with the run's row (status running)."""
    row = start(job, by)
    task = asyncio.get_running_loop().create_task(execute(row["id"]))
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)
    return row


async def settle() -> None:
    """Wait for the runs in flight (the tests)."""
    while _TASKS:
        await asyncio.gather(*list(_TASKS), return_exceptions=True)


def get(run_id: str) -> Dict[str, Any]:
    with db.tx() as con:
        r = con.execute("select * from job_runs where id = ?", (run_id,)).fetchone()
    if r is None:
        raise KeyError(run_id)
    return _row(r)


def recent(limit: int = 20) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from job_runs order by created desc limit ?", (limit,)).fetchall()
    return [_row(r) for r in rows]


def _set(con, r, status: str, **fields) -> None:
    import json

    data = {**json.loads(r["data"]), **fields}
    con.execute("update job_runs set status = ?, data = ? where id = ?", (status, db.dumps(data), r["id"]))

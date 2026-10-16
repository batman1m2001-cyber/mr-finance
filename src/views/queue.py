"""The agent run queue (BRD-RULE-AI-13; BRD completion F6): a CIO's “Chạy Agent CIO” queues a job and answers at
once; the ``agent_worker`` job (every 5 seconds, one run at a time) runs the same graph as before
(``cio_agent_flow``) and records how it went; the event page follows the job.

``agent_jobs``: one row per request — queued → running → done (with the view) or failed (with why). One open job
per event: asking again returns the one waiting. A job left running by a worker that died is failed after
``STALE_S``, so the event can be run again.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from control import audit, db, roles
from control.errors import Conflict
from events import store as events
from views import agents

STALE_S = 30 * 60


def _row(r) -> Dict[str, Any]:
    return db.load(r)


def enqueue(event_id: str, by: str, mode: Optional[str] = None) -> Dict[str, Any]:
    """Checked now (who, which event, which mode), run later. The checks the run makes again are the same."""
    roles.require(by, "cio")
    ev = events.get(str(event_id))
    if ev["blocked"]:
        raise Conflict(f"Sự kiện {ev['id']} đang bị giữ chờ Tuân thủ: {', '.join(ev['held'])}")
    try:
        run_mode = agents.resolve_mode(mode)
    except agents.AgentError as exc:
        raise Conflict(str(exc)) from None
    now = time.time()
    with db.tx() as con:
        open_ = con.execute(
            "select * from agent_jobs where event_id = ? and status in ('queued', 'running') order by created desc",
            (ev["id"],),
        ).fetchone()
        if open_ is not None:
            return {**_row(open_), "queued": False}
        seq = db.next_seq(con, "agent_job")
        jid = f"AJ-{seq:06d}"
        data = {"by": by, "mode": run_mode, "asked_mode": mode}
        con.execute("insert into agent_jobs values (?, ?, 'queued', ?, ?)", (jid, ev["id"], now, db.dumps(data)))
        audit.append(con, by, "agent.queued", jid, {"event": ev["id"], "mode": run_mode})
    return {**get(jid), "queued": True}


def get(job_id: str) -> Dict[str, Any]:
    with db.tx() as con:
        r = con.execute("select * from agent_jobs where id = ?", (job_id,)).fetchone()
    if r is None:
        raise KeyError(job_id)
    return _row(r)


def for_event(event_id: str) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from agent_jobs where event_id = ? order by created", (event_id,)).fetchall()
    return [_row(r) for r in rows]


def waiting() -> int:
    with db.tx() as con:
        return con.execute("select count(*) from agent_jobs where status in ('queued', 'running')").fetchone()[0]


def claim() -> Optional[Dict[str, Any]]:
    """The oldest queued job, marked running (a job running past ``STALE_S`` is failed first)."""
    from control import alerts

    now = time.time()
    with db.tx() as con:
        stale = con.execute(
            "select * from agent_jobs where status = 'running' and json_extract(data, '$.started') < ?",
            (now - STALE_S,),
        ).fetchall()
        for r in stale:
            _set(con, r, "failed", error="Không xong sau 30 phút (tiến trình chạy đã dừng)", finished=now)
        r = con.execute("select * from agent_jobs where status = 'queued' order by created limit 1").fetchone()
        if r is not None:
            _set(con, r, "running", started=now)
    for s in stale:
        alerts.raise_("agent", "queue", f"Lần chạy {s['id']} không xong sau 30 phút", "Tiến trình chạy đã dừng")
    return get(r["id"]) if r is not None else None


def finish(job_id: str, view_id: Optional[str], error: Optional[str]) -> Dict[str, Any]:
    with db.tx() as con:
        r = con.execute("select * from agent_jobs where id = ?", (job_id,)).fetchone()
        _set(con, r, "failed" if error else "done", view_id=view_id, error=error, finished=time.time())
        audit.append(con, "agent", "agent.job_done", job_id, {"view": view_id, "error": error})
    if error:  # a run that did not finish its own record (a crash) still alerts (NFR-12)
        from control import alerts

        alerts.raise_("agent", "queue", f"Lần chạy {job_id} của sự kiện {r['event_id']} lỗi", error)
    return get(job_id)


def _set(con, r, status: str, **fields) -> None:
    import json

    data = {**json.loads(r["data"]), **fields}
    con.execute("update agent_jobs set status = ?, data = ? where id = ?", (status, db.dumps(data), r["id"]))

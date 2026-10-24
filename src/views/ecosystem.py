"""The Agent Ecosystem Map (A7, ADR-0033; OWN-AS-20…22): the person, the assistant and its tools, the background
agents, the CIO desk, the rules and the stores, with the connections the code makes and each part's state from what
it recorded.

- **Nodes** are fixed here; their **state** is read from records, never guessed: the assistant's turns
  (``audit_log`` ``assistant.turn``, without their text) and the writes waiting on a person (``parked``); the
  agents' runs (``agent_runs``) and the queue (``agent_jobs``); the consolidator's runs (``consolidations``); the
  follow-ups (``follow_ups``); and every scheduled job's own run records (``.operonx/jobs/<job>/<run>/run.json``),
  whose items name their traces. ``active`` — running now; ``waiting`` — queued, or waiting on a person or a
  condition; ``done`` — the last run ended well; ``failed`` — it did not; ``idle`` — never ran.
- **Edges** are only what the code does: each names the file and the symbol that makes it (``code``), and a test
  checks both exist. Nothing is drawn for looks.
- **Drill-down**: a node's runs (``runs``), and one run's steps (``run``) — each op's status and time from the
  trace, an agent run's nodes, a turn's tools — never a prompt, a question or an answer.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from control import db

ROOT = Path(__file__).resolve().parents[2]
DAY = 86400.0
RUNS = 20  # a node's runs, newest first
STATES = {"active": "Đang chạy", "waiting": "Đang chờ", "done": "Hoàn tất", "failed": "Lỗi", "idle": "Chưa chạy"}

GROUPS = [
    {"id": "person", "label": "Người dùng", "note": "sáu vai trò, mỗi người chỉ thấy phần được phép"},
    {"id": "front", "label": "Cửa trước", "note": "trợ lý và công cụ của nó: mỗi câu hỏi đi qua đây"},
    {"id": "data", "label": "Dữ liệu", "note": "nơi các phần đọc và ghi"},
    {"id": "cio", "label": "Bàn CIO", "note": "nhận định thị trường, có cổng duyệt"},
    {"id": "rules", "label": "Luật", "note": "kiểm tra tất định, không gọi mô hình"},
    {"id": "background", "label": "Chạy nền", "note": "theo lịch, cho từng người"},
]

# the assistant's tools, by the module that holds them (every registry tool is in exactly one: a test checks)
TOOL_FAMILIES = {
    "tools_app": (
        "assistant.tools",
        "assistant.actions",
        "assistant.graphtools",
        "assistant.desktools",
        "assistant.dataroom",
    ),
    "tools_memory": ("assistant.memory",),
    "tools_knowledge": ("assistant.knowledge",),
    "tools_follow": ("assistant.followups",),
}

NODES: List[Dict[str, Any]] = [
    {"id": "person", "group": "person", "label": "Người dùng", "icon": "user",
     "does": "Hỏi trợ lý, xác nhận mọi việc ghi; CIO chạy Agent CIO, Tuân thủ yêu cầu tóm tắt chính sách; nhận "
             "thông báo theo dõi ở chuông."},
    {"id": "assistant", "group": "front", "label": "OneWealth Copilot", "icon": "sparkles", "model": "copilot",
     "does": "Hiểu câu hỏi, gọi công cụ của vai trò qua nhiều bước, dừng chờ người xác nhận trước khi ghi, trả lời "
             "kèm trang, nguồn và ngày (A2).",
     "reads": "kết quả công cụ khi client_ai cho phép; nếu không, chỉ câu hỏi đã che và trạng thái công cụ"},
    {"id": "fallback", "group": "front", "label": "Bộ định tuyến dự phòng", "icon": "flow",
     "does": "Khi chưa có mô hình hoặc mô hình lỗi trước công cụ đầu: chọn một công cụ theo từ khoá (Copilot), "
             "để sản phẩm không dừng vì AI (NFR-03).",
     "reads": "câu hỏi đã che tên và số"},
    {"id": "tools_app", "group": "front", "label": "Công cụ của ứng dụng", "icon": "layers",
     "does": "Chạy đúng đồ thị mà các trang chạy: tổng quan, dòng tiền, tác động, đề xuất, sự kiện, cảnh báo…; "
             "đếm, lọc bằng truy_van trên phòng dữ liệu chỉ đọc của vai trò (ADR-0040)."},
    {"id": "tools_memory", "group": "front", "label": "Trí nhớ", "icon": "history",
     "does": "Nhớ, sửa, quên những gì người dùng bảo và xác nhận; tìm lại hội thoại cũ (A4)."},
    {"id": "tools_follow", "group": "front", "label": "Theo dõi", "icon": "bell",
     "does": "Đặt, liệt kê, huỷ một điều kiện cần báo: mức của chuỗi thị trường, hoặc một chủ đề (A6)."},
    {"id": "tools_knowledge", "group": "front", "label": "Hướng dẫn, tài liệu, web", "icon": "info",
     "does": "Hướng dẫn sử dụng và cách tính; tài liệu người dùng tải lên; tìm trên web với câu hỏi đã che (A5)."},
    {"id": "news", "group": "data", "label": "Tin tức", "icon": "news", "jobs": ("news_ingest",),
     "does": "Tin RSS trong danh sách trắng, qua các cổng, vào hộp tin của CIO mỗi 10 phút."},
    {"id": "state", "group": "data", "label": "Dữ liệu ứng dụng", "icon": "lock", "store": "data/state.db",
     "does": "Khách hàng và danh mục (mã hoá theo cột), sự kiện, nhận định, cảnh báo, nhật ký kiểm toán."},
    {"id": "market", "group": "data", "label": "Thị trường", "icon": "stock",
     "jobs": ("market_equity", "market_flows", "market_yields", "market_fx", "market_world", "market_gold",
              "market_crypto"),
     "does": "Giá đóng cửa và chuỗi công khai, mỗi nguồn theo lịch riêng (F1)."},
    {"id": "assistant_db", "group": "data", "label": "Hội thoại và trí nhớ", "icon": "inbox",
     "store": "data/assistant.db",
     "does": "Hội thoại (mã hoá), việc ghi đang chờ, mục trí nhớ, việc theo dõi, lần tổng hợp."},
    {"id": "kb", "group": "data", "label": "Tri thức", "icon": "file", "store": "data/kb",
     "does": "Hướng dẫn theo vai trò và trang, cách tính, thuật ngữ, tài liệu của từng người."},
    {"id": "web", "group": "data", "label": "Web", "icon": "link", "store": "OpenRouter",
     "does": "Tìm kiếm web của OpenRouter: chỉ nhận câu hỏi đã che, trả về đường dẫn trích dẫn."},
    {"id": "queue", "group": "cio", "label": "Hàng đợi agent", "icon": "list",
     "does": "Lệnh “Chạy Agent CIO” vào hàng đợi; mỗi 5 giây chạy việc cũ nhất, mỗi lần một việc (AI-13)."},
    {"id": "cio", "group": "cio", "label": "Agent CIO", "icon": "bot", "model": "cio", "agent": "cio",
     "does": "Một sự kiện → bốn nhóm phân tích song song → thảo luận → tổng hợp 2–4 kịch bản (FR-301…303).",
     "reads": "tin của sự kiện, nghiên cứu đã phát hành — không dữ liệu khách"},
    {"id": "challenger", "group": "cio", "label": "Agent Phản biện", "icon": "shield", "model": "challenger",
     "agent": "challenger",
     "does": "Kiểm tra nhận định trước khi duyệt, và lại khi CIO sửa (FR-303).",
     "reads": "nhận định và sự kiện — không dữ liệu khách"},
    {"id": "policy", "group": "cio", "label": "Agent Chính sách", "icon": "scale", "model": "cio", "agent": "policy",
     "does": "Tóm tắt văn bản chính sách đã xác nhận nguồn, trích đúng điều khoản (FR-306).",
     "reads": "một văn bản chính sách — không danh mục, không dữ liệu khách"},
    {"id": "follow_checks", "group": "rules", "label": "Kiểm tra theo dõi", "icon": "eye",
     "does": "Sau mỗi lần tải thị trường và nhận tin: so điều kiện đang mở, báo một lần (A6)."},
    {"id": "policy_sweep", "group": "rules", "label": "Quét chính sách", "icon": "alert", "jobs": ("policy_sweep",),
     "does": "07:00 hằng ngày: cảnh báo chính sách, vĩ mô, hạ tầng cho từng khách hàng."},
    {"id": "consolidator", "group": "background", "label": "Tổng hợp trí nhớ", "icon": "zap", "model": "copilot",
     "jobs": ("assistant_consolidate",),
     "does": "Mỗi 5 phút: hội thoại nhàn rỗi 15 phút → tối đa 5 mục trí nhớ, kiểm như người dùng tự bảo nhớ (A6).",
     "reads": "hội thoại của chính người đó, chỉ nơi mô hình được đọc"},
    {"id": "retention", "group": "background", "label": "Lưu giữ", "icon": "clock", "jobs": ("assistant_retention",),
     "does": "02:30 hằng ngày: xoá hội thoại quá hạn lưu giữ của Tuân thủ và mục trí nhớ hết hạn (A4)."},
]  # fmt: skip

EDGES: List[Dict[str, str]] = [
    {"from": "person", "to": "assistant", "label": "hỏi; xác nhận việc ghi", "code": "app/main.py::assistant_flow"},
    {"from": "assistant", "to": "fallback", "label": "khi không có mô hình, hoặc mô hình lỗi trước công cụ đầu",
     "code": "src/assistant/ops.py::fallback"},
    {"from": "assistant", "to": "tools_app", "label": "gọi công cụ của vai trò",
     "code": "src/assistant/registry.py::agent_tools"},
    {"from": "assistant", "to": "tools_memory", "label": "gọi công cụ của vai trò",
     "code": "src/assistant/registry.py::agent_tools"},
    {"from": "assistant", "to": "tools_knowledge", "label": "gọi công cụ của vai trò",
     "code": "src/assistant/registry.py::agent_tools"},
    {"from": "assistant", "to": "tools_follow", "label": "gọi công cụ của vai trò",
     "code": "src/assistant/registry.py::agent_tools"},
    {"from": "fallback", "to": "tools_app", "label": "một công cụ theo từ khoá",
     "code": "src/copilot/ops.py::run_tool"},
    {"from": "assistant", "to": "assistant_db", "label": "lưu hội thoại; đọc trí nhớ vào lời dặn",
     "code": "src/assistant/conversations.py::record"},
    {"from": "tools_app", "to": "state", "label": "đọc, ghi qua đồ thị của các trang",
     "code": "src/assistant/base.py::run_graph"},
    {"from": "tools_app", "to": "news", "label": "lấy tin ngay (CIO)", "code": "src/assistant/tools.py::ingest_flow"},
    {"from": "tools_memory", "to": "assistant_db", "label": "nhớ, sửa, quên; tìm hội thoại cũ",
     "code": "src/assistant/memory.py::store"},
    {"from": "tools_knowledge", "to": "kb", "label": "hướng dẫn, cách tính, tài liệu",
     "code": "src/assistant/knowledge.py::kb"},
    {"from": "tools_knowledge", "to": "web", "label": "câu hỏi đã che", "code": "src/assistant/web.py::query_of"},
    {"from": "tools_follow", "to": "assistant_db", "label": "đặt, liệt kê, huỷ theo dõi",
     "code": "src/assistant/followups.py::create"},
    {"from": "consolidator", "to": "assistant_db", "label": "đọc hội thoại nhàn rỗi; ghi ≤ 5 mục trí nhớ",
     "code": "src/assistant/consolidate.py::keep"},
    {"from": "retention", "to": "assistant_db", "label": "xoá quá hạn lưu giữ",
     "code": "src/assistant/retention.py::sweep"},
    {"from": "market", "to": "follow_checks", "label": "sau mỗi lần tải: chuỗi của job",
     "code": "src/market/graph.py::follow_ups_market"},
    {"from": "news", "to": "follow_checks", "label": "sau mỗi lần nhận tin: sự kiện đã duyệt",
     "code": "src/news/graph.py::follow_ups_topics"},
    {"from": "follow_checks", "to": "person", "label": "báo một lần ở chuông", "code": "web/header.js::follow_up_seen"},
    {"from": "policy_sweep", "to": "state", "label": "nhận định đã duyệt và danh mục → cảnh báo khách",
     "code": "src/impact/graph.py::alerts_flow"},
    {"from": "person", "to": "queue", "label": "CIO: “Chạy Agent CIO” cho một sự kiện",
     "code": "app/main.py::agent_queue_flow"},
    {"from": "queue", "to": "cio", "label": "chạy việc cũ nhất", "code": "src/views/worker.py::run_next"},
    {"from": "news", "to": "cio", "label": "tin của sự kiện", "code": "src/views/ops.py::gather"},
    {"from": "cio", "to": "challenger", "label": "phản biện trước khi duyệt", "code": "src/views/ops.py::review"},
    {"from": "cio", "to": "state", "label": "nhận định chờ CIO duyệt", "code": "src/views/ops.py::save_view"},
    {"from": "person", "to": "policy", "label": "Tuân thủ: tóm tắt một văn bản",
     "code": "app/main.py::policy_summarise_flow"},
    {"from": "policy", "to": "state", "label": "tóm tắt, trích điều khoản", "code": "src/policy/agent.py::summarise"},
]  # fmt: skip

# the main path of a question, start to answer (brief §4): each step names the nodes it lights
FLOW = [
    {"step": "Hỏi", "nodes": ["person", "assistant"], "note": "câu hỏi, trang đang mở, vai trò"},
    {"step": "Chọn công cụ", "nodes": ["assistant", "fallback"], "note": "mô hình chọn; không có mô hình: từ khoá"},
    {"step": "Đọc dữ liệu được phép", "nodes": ["tools_app", "tools_memory", "tools_knowledge", "state", "kb"],
     "note": "đúng quyền của người hỏi"},
    {"step": "Ghi: chờ xác nhận", "nodes": ["assistant", "person"], "note": "một dòng để xác nhận, rồi đọc lại"},
    {"step": "Trả lời có nguồn", "nodes": ["assistant", "assistant_db"], "note": "trang, nguồn, ngày; ghi nhật ký"},
]  # fmt: skip


# -- the records ---------------------------------------------------------------------------------------------------


def job_dir(name: str) -> Path:
    """Where a job records its runs — asked of the job itself (``.operonx/jobs/<job>`` under the project)."""
    from app.main import APP

    return Path(APP.job(name).records()) / name


def traces_root() -> Path:
    from operonx.telemetry.consumers.local import resolve_root

    return resolve_root("")


_FINISHED: Dict[str, Dict[str, Any]] = {}  # a finished run's record never changes: read once per process


def _epoch(iso: Optional[str]) -> Optional[float]:
    return datetime.fromisoformat(iso).timestamp() if iso else None


def _job_run(path: Path) -> Optional[Dict[str, Any]]:
    key = str(path)
    if key in _FINISHED:
        return _FINISHED[key]
    try:
        r = json.loads((path / "run.json").read_text("utf-8"))
    except (OSError, ValueError):
        return None
    run = {"id": f"{r['job']}/{r['run_id']}", "job": r["job"], "status": r["status"], "at": _epoch(r.get("started")),
           "ended": _epoch(r.get("ended")), "counts": r.get("counts") or {}, "error": r.get("error"),
           "by": (r.get("trigger") or {}).get("by")}  # fmt: skip
    if r["status"] != "running":
        _FINISHED[key] = run
    return run


def job_runs(jobs, since: Optional[float] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """The jobs' run records, newest first: those started since ``since``, at most ``limit``. A run's folder is
    named for its UTC start, so the folders alone say which to read."""
    cut = time.strftime("%Y%m%dT%H%M%S", time.gmtime(since)) if since else ""
    names = []
    for job in jobs:
        d = job_dir(job)
        if d.is_dir():
            names += [(p.name, p) for p in d.iterdir() if p.is_dir() and p.name >= cut]
    names.sort(key=lambda x: x[0], reverse=True)
    out = []
    for _, p in names[:limit] if limit else names:
        r = _job_run(p)
        if r is not None:
            out.append(r)
    return out


def _job_state(r: Optional[Dict[str, Any]]) -> str:
    if r is None:
        return "idle"
    return {"running": "active", "ok": "done"}.get(r["status"], "failed")


def _turns(since: float, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """The assistant's turns from the audit log: who acted in which role, the mode, the tools and their statuses,
    tokens and cost — never the question or the answer (they are not there)."""
    with db.tx() as con:
        rows = con.execute(
            "select seq, ts, data from audit_log where action = 'assistant.turn' and ts >= ? order by seq desc"
            + (f" limit {int(limit)}" if limit else ""),
            (since,),
        ).fetchall()
    return [{"seq": r["seq"], "at": r["ts"], **json.loads(r["data"])} for r in rows]


def _turn_state(status: Optional[str]) -> str:
    return {"failed": "failed", "pending": "waiting"}.get(status or "", "done")


def _parked(now: float) -> int:
    from assistant import conversations as conv
    from assistant import turn as turns

    with conv.db() as con:
        if not conv._has(con, "parked"):
            return 0
        return con.execute("select count(*) from parked where created > ?", (now - turns.APPROVAL_TTL,)).fetchone()[0]


def _agent_runs(agent: str, since: float = 0.0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute(
            "select id, subject_id, created, data from agent_runs where agent = ? and created >= ?"
            " order by created desc" + (f" limit {int(limit)}" if limit else ""),
            (agent, since),
        ).fetchall()
    out = []
    for r in rows:
        d = json.loads(r["data"])
        out.append({"id": r["id"], "subject": r["subject_id"], "at": r["created"], "status": d.get("status"),
                    "mode": d.get("mode"), "model": d.get("model"), "error": d.get("error") or None,
                    "ended": d.get("finished"), "nodes": d.get("nodes") or []})  # fmt: skip
    return out


def _agent_state(r: Optional[Dict[str, Any]]) -> str:
    if r is None:
        return "idle"
    return {"running": "active", "ok": "done"}.get(r["status"], "failed")


def _queue(since: float = 0.0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute(
            "select * from agent_jobs where created >= ? order by created desc"
            + (f" limit {int(limit)}" if limit else ""),
            (since,),
        ).fetchall()
    return [db.load(r) for r in rows]


def _consolidations(since: float = 0.0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    from assistant import consolidate
    from assistant import conversations as conv

    with conv.db() as con:
        consolidate._ensure(con)
        rows = con.execute(
            "select id, status, attempts, started, finished, tokens_in, tokens_out, cost, added, merged, refused, error"
            " from consolidations where started >= ? order by started desc" + (f" limit {int(limit)}" if limit else ""),
            (since,),
        ).fetchall()
    return [dict(r) for r in rows]


def _follow_ups() -> Dict[str, Any]:
    from assistant import conversations as conv
    from assistant import followups

    with conv.db() as con:
        followups._ensure(con)
        counts = dict(con.execute("select status, count(*) from follow_ups group by status").fetchall())
        rows = con.execute(
            "select id, kind, series, op, status, created, fired_at from follow_ups"
            " order by coalesce(fired_at, created) desc limit ?",
            (RUNS,),
        ).fetchall()
    return {"counts": counts, "rows": [dict(r) for r in rows]}


# -- the map -------------------------------------------------------------------------------------------------------


def _tools() -> Dict[str, List[Dict[str, Any]]]:
    from assistant import registry

    out: Dict[str, List[Dict[str, Any]]] = {k: [] for k in TOOL_FAMILIES}
    for name, t in registry.REGISTRY.items():
        fam = next(k for k, mods in TOOL_FAMILIES.items() if t.run.__module__ in mods)
        out[fam].append({"name": name, "label": registry.LABELS.get(name, name), "write": t.write,
                         "roles": list(t.roles), "page": t.page, "paid": t.cost != "free"})  # fmt: skip
    return out


def _models() -> Dict[str, Optional[str]]:
    from copilot import router
    from views import agents

    st = agents.models()
    live = agents.configured_mode() == "live"
    return {"copilot": router.model() if router.live() else None,
            "cio": st.get("cio") if live else None, "challenger": st.get("challenger") if live else None}  # fmt: skip


def _tally(states: List[str]) -> Dict[str, int]:
    return {"runs": len(states), "failed": sum(s == "failed" for s in states)}


def states(now: Optional[float] = None) -> Dict[str, Dict[str, Any]]:
    """Each node's state, its last run's time and the last day's runs, from the records above."""
    now = time.time() if now is None else now
    since = now - DAY
    out: Dict[str, Dict[str, Any]] = {}

    turns = _turns(since)
    last_turn = _turns(0.0, limit=1)
    parked = _parked(now)
    lt = last_turn[0] if last_turn else None
    out["assistant"] = {"state": "waiting" if parked else (_turn_state(lt["status"]) if lt else "idle"),
                        "at": lt and lt["at"], "waiting": parked,
                        "day": _tally([_turn_state(t["status"]) for t in turns])}  # fmt: skip
    fb = [t for t in turns if t.get("mode") == "fallback"]
    out["fallback"] = {"state": _turn_state(fb[0]["status"]) if fb else "idle", "at": fb[0]["at"] if fb else None,
                       "day": _tally([_turn_state(t["status"]) for t in fb])}  # fmt: skip
    tools = _tools()
    for fam, items in tools.items():
        names = {t["name"] for t in items}
        calls = [(t["at"], s) for t in turns for tool, s in t.get("steps") or [] if tool in names]
        st = [{"ok": "done", "pending": "waiting"}.get(s, "failed" if s in ("failed", "error") else "done")
              for _, s in calls]  # fmt: skip
        out[fam] = {"state": st[0] if st else "idle", "at": calls[0][0] if calls else None, "day": _tally(st),
                    "tools": len(items)}  # fmt: skip

    for n in NODES:
        if n.get("agent"):
            runs = _agent_runs(n["agent"], since)
            last = runs[0] if runs else (_agent_runs(n["agent"], limit=1) or [None])[0]
            out[n["id"]] = {"state": _agent_state(last), "at": last and last["at"],
                            "day": _tally([_agent_state(r) for r in runs])}  # fmt: skip
        elif n.get("jobs"):
            runs = job_runs(n["jobs"], since)
            # each job's last run, however old: a node with several jobs is as well as the worst of them
            st = [_job_state(r) for j in n["jobs"] for r in job_runs([j], limit=1)]
            state = next((s for s in ("active", "failed", "done") if s in st), "idle")
            out[n["id"]] = {"state": state, "at": runs[0]["at"] if runs else None,
                            "day": _tally([_job_state(r) for r in runs])}  # fmt: skip

    q = _queue(since)
    lq = q[0] if q else (_queue(limit=1) or [None])[0]
    open_ = [j for j in q if j["status"] in ("queued", "running")]
    qs = "active" if any(j["status"] == "running" for j in open_) else "waiting" if open_ else (
        {"done": "done", "failed": "failed"}.get(lq["status"], "done") if lq else "idle")  # fmt: skip
    out["queue"] = {"state": qs, "at": lq and lq["created"], "waiting": len(open_),
                    "day": _tally([{"failed": "failed"}.get(j["status"], "done") for j in q])}  # fmt: skip

    cons = _consolidations(since)
    job = out["consolidator"]
    lc = cons[0] if cons else (_consolidations(limit=1) or [None])[0]
    if job["state"] != "active" and lc is not None:  # the job ran well; a conversation it failed on still shows
        job["state"] = "failed" if lc["status"] == "failed" else "done"
    job["conversations"] = _tally(["failed" if c["status"] == "failed" else "done" for c in cons])
    job["cost"] = round(sum(c["cost"] or 0 for c in cons), 6)

    fu = _follow_ups()
    fired = [r for r in fu["rows"] if r["fired_at"]]
    out["follow_checks"] = {"state": "waiting" if fu["counts"].get("open") else "done" if fired else "idle",
                            "at": fired[0]["fired_at"] if fired else None, "waiting": fu["counts"].get("open", 0),
                            "day": {"runs": sum(1 for r in fired if r["fired_at"] >= since), "failed": 0}}  # fmt: skip
    return out


def ecosystem(now: Optional[float] = None) -> Dict[str, Any]:
    """The map: groups, nodes with their state, the edges with the code behind each, the main path of a question."""
    now = time.time() if now is None else now
    st = states(now)
    models = _models()
    tools = _tools()
    nodes = []
    for n in NODES:
        node = {k: v for k, v in n.items() if k not in ("jobs",)}
        node.update(st.get(n["id"]) or {"state": None})  # a store or the person has no runs of its own
        if n.get("model"):
            node["model"] = models.get(n["model"])
            node["resource"] = f"llm:{n['model']}"
        if n["id"] in tools:
            t = tools[n["id"]]
            node["kinds"] = {"read": sum(not x["write"] for x in t), "write": sum(x["write"] for x in t),
                             "paid": sum(x["paid"] for x in t)}  # fmt: skip
        if n.get("jobs"):
            node["jobs"] = list(n["jobs"])
        nodes.append(node)
    return {"as_of": now, "groups": GROUPS, "nodes": nodes, "edges": EDGES, "flow": FLOW, "states": STATES}


# -- drill-down: a node's runs, a run's steps ----------------------------------------------------------------------


def _row(rid: str, at: Optional[float], state: str, title: str, sub: str = "", ms: Optional[float] = None):
    return {"id": rid, "at": at, "state": state, "title": title, "sub": sub, "ms": ms}


def _ms(a: Optional[float], b: Optional[float]) -> Optional[float]:
    return round((b - a) * 1000) if a and b else None


def runs(node_id: str) -> Dict[str, Any]:
    """A node's last runs, newest first, as rows the drawer lists; a tool family lists its tools as well."""
    node = next((n for n in NODES if n["id"] == node_id), None)
    if node is None:
        raise KeyError(node_id)
    rows: List[Dict[str, Any]] = []
    extra: Dict[str, Any] = {}
    if node_id in ("assistant", "fallback") or node_id in TOOL_FAMILIES:
        turns = _turns(0.0, limit=200)
        if node_id == "fallback":
            turns = [t for t in turns if t.get("mode") == "fallback"]
        if node_id in TOOL_FAMILIES:
            fam = _tools()[node_id]
            names = {t["name"] for t in fam}
            turns = [t for t in turns if any(tool in names for tool, _ in t.get("steps") or [])]
            extra["tools"] = fam
        for t in turns[:RUNS]:
            tools = ", ".join(f"{tool} ({s})" for tool, s in t.get("steps") or []) or "không gọi công cụ"
            rows.append(_row(f"T{t['seq']}", t["at"], _turn_state(t["status"]), f"{t.get('role')} · {t.get('mode')}",
                             tools))  # fmt: skip
    elif node.get("agent"):
        for r in _agent_runs(node["agent"], limit=RUNS):
            sub = r["error"] or f"{len(r['nodes'])} bước · {r['model'] or '—'}"
            rows.append(_row(r["id"], r["at"], _agent_state(r), f"{r['subject']} · {r['mode']}", sub,
                             _ms(r["at"], r["ended"])))  # fmt: skip
    elif node_id == "queue":
        for j in _queue(limit=RUNS):
            d = j.get("data") or {}
            state = {"queued": "waiting", "running": "active", "failed": "failed"}.get(j["status"], "done")
            rows.append(_row(j["id"], j["created"], state, f"sự kiện {j['event_id']}",
                             d.get("error") or d.get("view_id") or j["status"]))  # fmt: skip
    elif node_id == "follow_checks":
        for f in _follow_ups()["rows"]:
            side = "trên" if f["op"] == "above" else "dưới"
            what = f"{f['series']} {side} mức" if f["kind"] == "market" else "chủ đề"
            how = {"open": "đang theo dõi", "fired": "đã báo"}.get(f["status"], f["status"])
            state = "waiting" if f["status"] == "open" else "done"
            rows.append(_row(f["id"], f["fired_at"] or f["created"], state, what, how))
    elif node.get("jobs"):
        for r in job_runs(node["jobs"], limit=RUNS):
            c = r["counts"]
            sub = f"{c.get('ok', 0)} ổn, {c.get('failed', 0)} lỗi" + (f" · {r['error']}" if r["error"] else "")
            rows.append(_row(r["id"], r["at"], _job_state(r), r["job"], sub, _ms(r["at"], r["ended"])))
        if node_id == "consolidator":
            extra["conversations"] = [
                _row(c["id"], c["started"], "failed" if c["status"] == "failed" else "done", c["status"],
                     c["error"] or f"+{c['added'] or 0} mục, gộp {c['merged'] or 0}, bỏ {c['refused'] or 0}"
                     f" · {(c['tokens_in'] or 0) + (c['tokens_out'] or 0)} token · US${c['cost'] or 0:.5f}",
                     _ms(c["started"], c["finished"]))
                for c in _consolidations(limit=RUNS)
            ]  # fmt: skip
    return {"node": node_id, "runs": rows, **extra}


_JOB_RUN = re.compile(r"^[a-z_]+/\d{8}T\d{6}-\d+$")


def _trace_steps(job: str, run_id: str, trace_id: str) -> List[Dict[str, Any]]:
    """One item's ops from its trace: name, status, time, the first line of an error — no inputs, no outputs."""
    path = traces_root() / "jobs" / job / run_id / trace_id / "nodes.jsonl"
    steps = []
    try:
        lines = path.read_text("utf-8").splitlines()
    except OSError:
        return steps
    for line in lines:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        err = (r.get("error") or "").strip().splitlines()
        steps.append({"name": r.get("op_name"), "status": "failed" if r.get("status") == "error" else "done",
                      "ms": round(r.get("duration_ms") or 0), "note": err[-1][:200] if err else ""})  # fmt: skip
    return steps


def run(node_id: str, run_id: str) -> Dict[str, Any]:
    """One run's steps: a job's items and each one's ops (from its trace), an agent run's nodes, a turn's tools."""
    node = next((n for n in NODES if n["id"] == node_id), None)
    if node is None:
        raise KeyError(node_id)
    if node.get("jobs") and _JOB_RUN.match(run_id):
        job, rid = run_id.split("/")
        if job not in node["jobs"]:
            raise KeyError(run_id)
        r = _job_run(job_dir(job) / rid)
        if r is None:
            raise KeyError(run_id)
        items = []
        try:
            lines = (job_dir(job) / rid / "items.jsonl").read_text("utf-8").splitlines()
        except OSError:
            lines = []
        for line in lines[:50]:
            it = json.loads(line)
            items.append({"key": it.get("key"), "state": "done" if it.get("status") == "ok" else "failed",
                          "ms": round(it.get("ms") or 0), "trace": it.get("trace_id"),
                          "steps": _trace_steps(job, rid, it["trace_id"]) if it.get("trace_id") else []})  # fmt: skip
        return {"kind": "job", "run": r, "state": _job_state(r), "items": items}
    if node.get("agent"):
        r = next((x for x in _agent_runs(node["agent"]) if x["id"] == run_id), None)
        if r is None:
            raise KeyError(run_id)
        steps = [{"name": f"{n.get('node')}" + (f" (lần {n['attempt']})" if (n.get("attempt") or 1) > 1 else ""),
                  "status": "failed" if n.get("error") else "done", "ms": n.get("ms"),
                  "note": n.get("error") or f"{n.get('model') or n.get('mode') or ''} · "
                          f"{(n.get('tokens_in') or 0) + (n.get('tokens_out') or 0)} token"}
                 for n in r["nodes"]]  # fmt: skip
        return {"kind": "agent", "run": {k: v for k, v in r.items() if k != "nodes"}, "state": _agent_state(r),
                "steps": steps}  # fmt: skip
    if run_id.startswith("T") and run_id[1:].isdigit():
        with db.tx() as con:
            row = con.execute(
                "select seq, ts, actor, data from audit_log where seq = ? and action = 'assistant.turn'",
                (int(run_id[1:]),),
            ).fetchone()
        if row is None:
            raise KeyError(run_id)
        d = json.loads(row["data"])
        from assistant import registry

        steps = [{"name": registry.LABELS.get(tool, tool), "ms": None, "note": tool,
                  "status": {"ok": "done", "pending": "waiting"}.get(s, "failed")}
                 for tool, s in d.get("steps") or []]  # fmt: skip
        return {"kind": "turn", "state": _turn_state(d.get("status")), "steps": steps,
                "run": {"id": run_id, "at": row["ts"], "role": d.get("role"), "mode": d.get("mode"),
                        "model": d.get("model"), "tokens": d.get("tokens"), "cost_usd": d.get("cost_usd"),
                        "audit_seq": row["seq"]}}  # fmt: skip
    raise KeyError(run_id)


def code_refs() -> List[str]:
    """Every ``path::symbol`` an edge names (the test checks each file holds its symbol)."""
    return sorted({e["code"] for e in EDGES})


def holds(ref: str) -> bool:
    path, symbol = ref.split("::")
    f = ROOT / path
    return f.is_file() and re.search(rf"\b{re.escape(symbol)}\b", f.read_text("utf-8")) is not None

"""The evidence steps: the frames as a role may read them, and the CIO's decision on one (NEWS_EVIDENCE_BRD §8.2)."""

from __future__ import annotations

from typing import Any, Dict

from operonx import op

from control.errors import BadRequest
from evidence import agent
from evidence import catalogue as cat
from evidence import frames


@op
def read(factor: str = None, role: str = None) -> dict:
    """Every frame (or one): a client and an RM read the approved ones without the CIO's marks; the CIO reads all of
    them, the review, which precedents have no source, the precedent calendar and the thresholds."""
    from people import auth

    seen = auth.role_for(role) or "rm"
    cio = seen == "cio"
    ids = [factor] if factor else frames.ids()
    if factor and factor not in frames.ids():
        raise BadRequest(f"không có nhận định cho {factor!r}")
    out: Dict[str, Any] = {
        "role": seen,
        "frames": [frames.view(f, cio) for f in ids if cio or frames.review(f)["status"] == "approved"],
    }
    if cio:
        out["calendar"] = {k: {"label": cat.EVENT_TYPES[k]["label"], "dates": v} for k, v in frames.data()["events"].items()}
        out["thresholds"] = {"min_precedents": cat.MIN_PRECEDENTS, "min_edge": cat.MIN_EDGE}
        kept = agent.drafts()
        out["drafts"] = sorted((agent.view(k, d) for k, d in kept.items()), key=lambda d: -d["at"])
        out["suggested"] = agent.suggested(set(kept))
    return {"evidence": out}


@op
def decide(factor: str = None, decision: str = None, by: str = None, note: str = "") -> dict:
    """The CIO approves, returns or rejects a frame; a returned or rejected one leaves the chart's evidence."""
    from control import roles

    u = roles.require(by, "cio")
    if factor not in frames.ids():
        raise BadRequest(f"không có nhận định cho {factor!r}")
    if decision not in frames.DECISIONS:
        raise BadRequest(f"decision là một trong {', '.join(frames.DECISIONS)}")
    return {"review": frames.decide(factor, decision, u["id"], note)}


@op
async def draft(news_id: str = None, by: str = None, mode: str = "") -> dict:
    """The evidence agent on one news item (§4, P1): its event type and a frame, checked (§9) and sent back with the
    reasons at most twice; the draft waits for the CIO. The agent reads the item, never a client's data."""
    from control import roles
    from control.errors import Conflict
    from news import store as news
    from views import agents

    roles.require(by, "cio")
    found = news.get([news_id]) if news_id else []
    if not found:
        raise BadRequest(f"không có tin {news_id!r}")
    item = found[0]
    try:
        run_mode = agents.resolve_mode(mode or None)
    except agents.AgentError as exc:
        raise Conflict(str(exc)) from None
    if run_mode == "mock":
        frame, why, attempts, calls = agent.mock(item, item.get("kind")), [], 1, []
    else:
        try:
            frame, why, attempts, calls = await agent.live(item, item.get("kind"))
        except agents.AgentError as exc:
            raise Conflict(f"Agent bằng chứng lỗi: {exc}") from None
    d = agent.draft(item, frame, why, run_mode, attempts, calls)
    agent.keep(item["id"], d)
    return {"draft": agent.view(item["id"], d)}


@op
def decide_draft(news_id: str = None, decision: str = None, by: str = None, note: str = "") -> dict:
    """The CIO approves, returns or rejects the agent's draft for a news item; a failed draft cannot be approved."""
    import time

    from control import audit, db, roles
    from control.errors import Conflict

    u = roles.require(by, "cio")
    kept = agent.drafts()
    if news_id not in kept:
        raise BadRequest(f"không có bản nháp cho {news_id!r}")
    if decision not in frames.DECISIONS:
        raise BadRequest(f"decision là một trong {', '.join(frames.DECISIONS)}")
    d = kept[news_id]
    if decision == "approve" and d["failed"]:
        raise Conflict("Bản nháp chưa qua kiểm tra: trả lại hoặc từ chối")
    d["review"] = {"status": frames.DECISIONS[decision], "by": u["id"], "at": time.time(), "note": str(note or "").strip()[:300]}
    agent.keep(news_id, d)
    with db.tx() as con:
        audit.append(con, u["id"], f"evidence.draft.{d['review']['status']}", news_id, {"note": d["review"]["note"]})
    return {"draft": agent.view(news_id, d)}

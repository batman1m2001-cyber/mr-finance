"""The steps of the CIO agent graph and of the CIO's decisions.

A step that fails inside the agent does not raise: it hands its error on, and ``save_view`` marks
the version AGENT_ERROR with the reason, so the CIO sees what failed (FR-301). A refused request
(wrong role, held event, bad decision) raises: the caller gets the reason as the run's error.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from operonx import op

from control import roles
from engine import default_model
from events import store as events
from news.ops import config as news_config
from views import agents, decide, schema
from views import store as vstore
from views.preview import preview


def public(view_id: str) -> Dict[str, Any]:
    """A view as the screens read it: the view, its challenges, decisions, agent runs, the approval
    checks and the market preview."""
    v = vstore.get(view_id)
    out = {
        "view": v,
        "challenges": vstore.challenges(view_id),
        "decisions": vstore.decisions(view_id),
        "runs": vstore.runs(view_id),
        "checks": decide.checks(v) if v.get("current") else [],
    }
    if v.get("current"):
        try:
            out["preview"] = preview(v["current"])
        except Exception as exc:  # noqa: BLE001 — a preview never hides the view
            out["preview_error"] = str(exc)
    return out


# -- the agent graph ---------------------------------------------------------------------------


@op
def gather(event_id: str, by: str = "cio", mode: Optional[str] = None) -> dict:
    """Deterministic inputs (BRD 8.1): the event's news and the market catalogue — never client data."""
    roles.require(by, "cio")
    ev = events.get(str(event_id))
    if ev["blocked"]:
        raise ValueError(f"Sự kiện {ev['id']} đang bị giữ chờ Tuân thủ: {', '.join(ev['held'])}")
    run_mode = agents.resolve_mode(mode)
    m = agents.models()
    view = vstore.create(ev["id"], by, run_mode, m if run_mode == "live" else {"cio": "mock", "challenger": "rules"})
    run_id = vstore.start_run("cio", view["id"], run_mode, m["cio"] if run_mode == "live" else "mock")
    packet = {
        "event": {"id": ev["id"], "title": ev["title"], "type": ev.get("type"), "factors": ev.get("factors", [])},
        "news": [
            {
                k: n.get(k)
                for k in ("id", "title", "summary", "outlet", "section", "label", "published", "factors", "event_type")
            }
            for n in ev["news"]
        ],
        "catalogue": schema.catalogue(),
    }
    return {"packet": packet, "view_id": view["id"], "run_id": run_id, "mode": run_mode}


@op
async def analyse(lens: str, packet: dict, mode: str, run_id: str) -> dict:
    """One analyst group (macro, equity, credit, other); the four run at once."""
    try:
        return {"note": await agents.analyst(lens, packet, mode, run_id, news_config()["factor_words"]), "error": ""}
    except agents.AgentError as exc:
        return {"note": None, "error": str(exc)}


@op
async def discuss(
    packet: dict,
    mode: str,
    run_id: str,
    macro: Optional[dict] = None,
    equity: Optional[dict] = None,
    credit: Optional[dict] = None,
    other: Optional[dict] = None,
    macro_error: str = "",
    equity_error: str = "",
    credit_error: str = "",
    other_error: str = "",
) -> dict:
    """The bull/bear debate, only when a row reaches ±2 or the groups disagree; at most two rounds."""
    notes = [macro, equity, credit, other]
    failed = "; ".join(e for e in (macro_error, equity_error, credit_error, other_error) if e)
    if failed or any(n is None for n in notes):
        return {"notes": [], "merged": None, "error": failed or "Một nhóm phân tích không trả kết quả"}
    try:
        return {"notes": notes, "merged": await agents.debate(notes, packet, mode, run_id), "error": ""}
    except agents.AgentError as exc:
        return {"notes": notes, "merged": None, "error": str(exc)}


@op
async def compose(
    packet: dict, mode: str, run_id: str, notes: Optional[list] = None, merged: Optional[dict] = None, error: str = ""
) -> dict:
    """Synthesis and the format check, with two retries."""
    if error:
        return {"view": None, "errors": [error]}
    names = {f.id: f.name for f in default_model().factors}
    try:
        view, errs = await agents.synthesize(packet, notes or [], merged or {"impacts": []}, mode, run_id, names)
    except agents.AgentError as exc:
        return {"view": None, "errors": [str(exc)]}
    return {"view": view, "errors": errs}


@op
def save_view(
    view_id: str, run_id: str, view: Optional[dict] = None, errors: Optional[list] = None, by: str = "cio"
) -> dict:
    """The draft kept (restricted tickers taken out of the rows), or AGENT_ERROR with why. (``view``
    has a default: a None output does not bind to an input.)"""
    errors = errors or []
    v = vstore.get(view_id)
    if view is None:
        vstore.finish_run(run_id, "error", "; ".join(errors))
        v["error"] = errors
        vstore.save(v, "AGENT_ERROR", by, "Sai định dạng sau 2 lần thử" if errors else "Lỗi agent")
        return {"view_id": view_id, "ok": False}
    restricted = [r["ticker"] for r in news_config()["restricted"]]
    keep, out = schema.split_restricted(view["impacts"], restricted)
    draft = {**view, "impacts": keep}
    v["draft"] = draft
    v["current"] = draft
    v["restricted_rows"] = out
    v["content_hash"] = vstore.content_hash(draft)
    vstore.finish_run(run_id, "ok")
    vstore.save(v, "PENDING_CHALLENGE", by, "Agent CIO viết xong")
    return {"view_id": view_id, "ok": True}


async def _challenge(view_id: str, by: str, stage: str) -> Dict[str, Any]:
    v = vstore.get(view_id)
    ev = events.get(v["event_id"])
    run_id = vstore.start_run("challenger", view_id, v["mode"], v["models"].get("challenger", "rules"))
    try:
        got = await agents.challenge(v["current"], ev, v["mode"], run_id)
    except agents.AgentError as exc:
        vstore.finish_run(run_id, "error", str(exc))
        raise ValueError(str(exc)) from None
    vstore.finish_run(run_id, "ok")
    independent = got["model"] != v["models"].get("cio")
    v.pop("challenge_error", None)
    ch = vstore.add_challenge(
        view_id, stage, {**got, "content_hash": v["content_hash"], "independent": independent, "run_id": run_id}
    )
    v = vstore.save(v, "PENDING_APPROVAL", by, f"Phản biện {ch['id']}: {len(got['findings'])} phát hiện")
    return ch


@op
async def review(view_id: str, ok: bool, by: str = "cio") -> dict:
    """The challenger, before approval (FR-303)."""
    if ok:
        await _challenge_or_note(view_id, by, "pre_approval")
    return {"result": public(view_id)}


async def _challenge_or_note(view_id: str, by: str, stage: str) -> None:
    """The challenger; when it fails the view stays PENDING_CHALLENGE with the error shown, and the
    CIO can run it again (action ``challenge``) — the CIO's draft is not lost."""
    try:
        await _challenge(view_id, by, stage)
    except ValueError as exc:
        v = vstore.get(view_id)
        v["challenge_error"] = str(exc)
        vstore.save(v, v["status"], by)


# -- the decisions -----------------------------------------------------------------------------


@op
async def decide_view(
    view_id: str,
    action: str,
    by: str,
    reason: str = "",
    idem_key: Optional[str] = None,
    edits: Optional[dict] = None,
    responses: Optional[dict] = None,
) -> dict:
    """One CIO action on a view (FR-304)."""
    roles.require(by, "cio")
    if action not in decide.ACTIONS:
        raise ValueError(f"action là một trong {', '.join(decide.ACTIONS)}")
    if idem_key:
        old = vstore.find_decision(idem_key)
        if old is not None:
            return {"result": public(old["view_id"]), "decision": {**old, "repeated": True}}
    v = vstore.get(str(view_id))
    if v["status"] not in decide.FROM[action]:
        raise ValueError(f"Không thể {action} khi nhận định ở trạng thái {v['status']}")
    if action == "edit":
        reason = decide._require_reason(reason, action)
        v = decide.apply_edit(v, edits or {}, by, reason)
        await _challenge_or_note(v["id"], by, "rechallenge")
        return {"result": public(v["id"]), "decision": None}
    if action == "challenge":
        await _challenge_or_note(v["id"], by, "rechallenge")
        return {"result": public(v["id"]), "decision": None}
    if action == "respond":
        decide.apply_responses(v, responses or {}, by)
        return {"result": public(v["id"]), "decision": None}
    reason = decide._require_reason(reason, action)
    if action == "approve":
        failed = [c for c in decide.checks(v) if not c["ok"]]
        if failed:
            raise ValueError("Chưa duyệt được: " + "; ".join(f"{c['label']} ({c['detail']})" for c in failed))
    dec = vstore.add_decision(
        v["id"], action, idem_key, {"by": by, "reason": reason, "content_hash": v.get("content_hash")}
    )
    if dec.get("repeated"):
        return {"result": public(v["id"]), "decision": dec}
    vstore.save(v, decide.TO[action], by, f"{dec['id']}: {reason}")
    if action == "approve":
        dec["superseded"] = decide.supersede_older(vstore.get(v["id"]), by)
    return {"result": public(v["id"]), "decision": dec}


def agent_status() -> Dict[str, Any]:
    """What the CIO screen says about the AI: which mode a run would use, and the two models."""
    m = agents.models()
    try:
        mode = agents.resolve_mode(None)
    except agents.AgentError:
        mode = "mock"
    return {
        "mode": mode,
        "models": m if mode == "live" else {"cio": "mock", "challenger": "rules"},
        "prompt_version": agents.PROMPT_VERSION,
    }


def event_views(event_id: str) -> List[Dict[str, Any]]:
    return [{k: v.get(k) for k in ("id", "version", "status", "mode", "created")} for v in vstore.for_event(event_id)]

"""The assistant's steps (A2): check → turn (operonx-agents, or the Copilot's path as the fallback) → answer."""

from __future__ import annotations

import base64
import binascii
import time
from typing import Any, Dict, List, Optional

from operonx import op
from operonx.core.loggings import LOGGER

from assistant import conversations as conv
from assistant import knowledge, memory, registry
from assistant import turn as turns
from assistant.base import Ctx
from control import audit, db, roles
from copilot import router
from copilot.ops import HELP, run_tool
from copilot.scrub import scrub
from people import auth

START = {
    **HELP,
    "specialist": ["Khuyến nghị nào đang chờ tôi duyệt?", "Tìm khách hàng"],
    "admin": ["Có cảnh báo hệ thống nào?", "Mở trang Hệ thống"],
}


@op
def check_request(
    message: str = None,
    role: str = None,
    client_id: str = None,
    scope: str = None,
    route: str = None,
    goals: list = None,
    turn_id: str = None,
    approvals: dict = None,
    conversation_id: str = None,
) -> dict:
    """Who asks (a customer always as client), what (≤ 2,000 characters), in which conversation (none: a new one),
    or which parked writes they answer."""
    message = str(message or "").strip()
    if len(message) > 2000:
        raise ValueError("Câu hỏi dài quá 2.000 ký tự")
    answers = {str(k): str(v) for k, v in (approvals or {}).items()}
    if any(v not in ("approve", "deny") for v in answers.values()):
        raise ValueError("Trả lời là approve hoặc deny")
    if answers and not turn_id:
        raise ValueError("Thiếu turn_id của việc đang chờ")
    if not message and not answers:
        raise ValueError("Hãy nhập câu hỏi")
    return {
        "request": {
            **who(role, client_id, scope),
            "message": message,
            "route": str(route or ""),
            "followed": None if goals is None else [str(g) for g in goals][:50],
            "turn_id": str(turn_id or "") or None,
            "approvals": answers,
            "conversation_id": str(conversation_id or "") or None,
        }
    }


def who(role: Optional[str], client_id: Optional[str], scope: Optional[str] = None) -> Dict[str, Any]:
    role = auth.role_for(str(role or "client"))
    if role not in registry.DEMO_USER:
        raise roles.Forbidden(f"vai trò {role!r} không có")
    return {"role": role, "client_id": client_id or None, "scope": scope or "personal"}


def context(r: Dict[str, Any]) -> Ctx:
    return Ctx(
        role=r["role"],
        client_id=r["client_id"],
        scope=r["scope"],
        question=r["message"],
        followed=r["followed"],
        user=auth.acting_id(registry.DEMO_USER.get(r["role"])),
        reads=turns.model_reads(),
        route=r["route"],
    )


async def fallback(r: Dict[str, Any], why: str) -> Dict[str, Any]:
    """The Copilot's path: the keyword router picks one tool, our code runs it; a write waits as there."""
    if r["approvals"]:
        return {"status": "failed", "mode": "fallback", "why": why, "steps": [],
                "text": "Không còn việc nào chờ xác nhận: trợ lý đang chạy chế độ dự phòng, hãy hỏi lại."}  # fmt: skip
    seen = scrub(r["message"])
    got = router.keyword(seen, r["route"])
    step = await run_tool(
        got["tool"], got["args"], False, r["role"], r["client_id"], r["scope"], r["message"], r["followed"]
    )
    out = {"status": step["status"], "mode": "fallback", "why": why, "seen": seen, "text": step["text"]}
    if step["status"] == "pending":  # the Copilot's own confirm (POST /api/copilot) runs it
        out["confirm"] = step["confirm"]
    out["steps"] = [] if step["status"] in ("pending", "unknown") else [step]
    out["suggest"] = step.get("suggest")
    return out


def conversation(r: Dict[str, Any], ctx: Ctx) -> str:
    """The conversation a message goes to: the one named, when it is this person's (else ValueError), or a new one."""
    if r["conversation_id"]:
        return conv.own(ctx, r["conversation_id"])["id"]
    return conv.start(ctx, r["message"])


@op
async def turn(request: dict) -> dict:
    """One turn: the agent when a model is configured; else, or when the model fails before any tool ran, the
    fallback. A parked write is answered only by the person who asked, within ten minutes. Every turn belongs to a
    conversation (A3): the one asked in, the one the parked write came from, or a new one."""
    r = request
    ctx = context(r)
    try:
        cid = None if r["approvals"] else conversation(r, ctx)
    except ValueError as exc:  # someone else's conversation, or one deleted
        return {"result": {"status": "failed", "mode": "model", "steps": [], "text": str(exc)}}
    if not turns.live():
        return {"result": {**await fallback(r, "chưa cấu hình mô hình cho trợ lý"), "conversation_id": cid}}
    try:
        if r["approvals"]:
            return {"result": await turns.resume(ctx, r["turn_id"], r["approvals"])}
        got = await turns.run(ctx, r["message"], cid)
        if got.get("model_error") and not ctx.trail:  # the model failed before any tool ran: NFR-03
            LOGGER.warning("assistant: the model failed (%s)", got["model_error"])
            why = f"mô hình lỗi ({got['model_error'].split(':')[0]})"
            return {"result": {**await fallback(r, why), "conversation_id": cid}}
        return {"result": got}
    except ValueError as exc:  # nothing waiting for this person, or too late
        return {"result": {"status": "failed", "mode": "model", "steps": [], "text": str(exc), "conversation_id": cid}}
    except Exception as exc:  # noqa: BLE001 - the model failed: NFR-03, the product keeps answering
        LOGGER.warning("assistant: the model failed (%s: %s)", type(exc).__name__, exc)
        if ctx.trail or r["approvals"]:
            return {
                "result": {
                    "status": "failed",
                    "mode": "model",
                    "steps": [],
                    "text": f"Trợ lý gặp lỗi giữa chừng ({type(exc).__name__}); "
                    "hãy kiểm tra trên trang trước khi làm lại.",
                    "conversation_id": cid,
                }
            }
        return {"result": {**await fallback(r, f"mô hình lỗi ({type(exc).__name__})"), "conversation_id": cid}}


def _latest(dates: List[str]) -> str | None:
    return max((d for d in dates if d), default=None)


@op
def answer(request: dict, result: dict) -> dict:
    """The answer with what it rests on (each step's page, sources and date), stamped and audited: who, the mode,
    the tools and their statuses, the model and its usage — not the conversation's text."""
    r = request
    steps = result.get("steps") or []
    seen_pages = set()
    citations = []
    for s in steps:
        ev = s.get("evidence")
        if ev and ev["route"] not in seen_pages:
            seen_pages.add(ev["route"])
            citations.append(ev)
    sources = list(dict.fromkeys(x for s in steps for x in s.get("sources") or [] if x))
    last = next((registry.REGISTRY.get(s["tool"]) for s in reversed(steps) if s.get("tool")), None)
    at = time.time()
    actor = auth.acting_id(registry.DEMO_USER.get(r["role"])) or f"client:{r['client_id'] or '-'}"
    usage = result.get("usage") or {}
    with db.tx() as con:
        seq = audit.append(
            con,
            actor,
            "assistant.turn",
            ",".join(s["tool"] for s in steps if s.get("tool")) or "-",
            {
                "role": r["role"],
                "client_id": r["client_id"],
                "status": result.get("status"),
                "mode": result.get("mode"),
                "model": result.get("model"),
                "steps": [[s.get("tool"), s.get("status")] for s in steps],
                "confirm": bool(r["approvals"]),
                "tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
                "cost_usd": usage.get("cost_usd"),
            },
        )
    out = {
        **result,
        "citations": citations,
        "sources": sources,
        "as_of": _latest([s.get("as_of") for s in steps]),
        "focus": next((s.get("focus") for s in reversed(steps) if s.get("focus")), []),
        "navigate": next((s.get("navigate") for s in reversed(steps) if s.get("navigate")), None),
        "suggest": result.get("suggest") or (last and last.follow) or START.get(r["role"], []),
        "answered_at": at,
        "audit_seq": seq,
    }
    if out.get("conversation_id"):  # the turn as the panel shows it, to draw again on any device (A3)
        conv.record(out["conversation_id"], r["message"] or None, out)
    return {"assistant": out}


# -- the conversations (A3): list, open, delete ------------------------------------------------------------------


@op
def conversations(action: str = None, conversation_id: str = None, role: str = None, client_id: str = None) -> dict:
    """The person's conversations in this role: ``list`` (newest first), ``open`` one (its turns as shown, and the
    writes still waiting in it), ``delete`` one (its turns and the model's side; audited without its text)."""
    r = {**who(role, client_id), "message": "", "route": "", "followed": None}
    ctx = context(r)
    action = str(action or "list")
    if action == "list":
        return {"conversations": {"items": conv.listing(ctx)}}
    if action == "open":
        c = conv.own(ctx, conversation_id)
        with conv.db() as con:
            rows = con.execute(
                "select run_id from parked where conversation_id = ? and created > ?",
                (c["id"], time.time() - turns.APPROVAL_TTL),
            ).fetchall()
        return {"conversations": {"conversation": c, "turns": conv.turns_of(c["id"]), "waiting": [x[0] for x in rows]}}
    if action == "delete":
        n = conv.delete(ctx, conversation_id)
        actor = auth.acting_id(registry.DEMO_USER.get(r["role"])) or f"client:{r['client_id'] or '-'}"
        with db.tx() as con:
            audit.append(
                con, actor, "assistant.conversation.delete", str(conversation_id), {"role": r["role"], "turns": n}
            )
        return {"conversations": {"deleted": conversation_id, "turns": n}}
    raise ValueError("action là list, open hoặc delete")


# -- the Bộ nhớ page (A4): list, correct, forget, forget all, search the archive ---------------------------------


@op
async def memory_page(
    action: str = None,
    item_id: str = None,
    text: str = None,
    kind: str = None,
    query: str = None,
    role: str = None,
    client_id: str = None,
    file_name: str = None,
    data: str = None,
    key: str = None,
) -> dict:
    """The person's long-term items, archive and documents in this role. Changes are audited with what changed, not
    the text. A document arrives base64-encoded (``file_name``, ``data``; not ``name``: the serve layer passes
    ``name`` to every graph)."""
    r = {**who(role, client_id), "message": "", "route": "", "followed": None}
    ctx = context(r)
    action = str(action or "list")
    actor = auth.acting_id(registry.DEMO_USER.get(r["role"])) or f"client:{r['client_id'] or '-'}"

    def audited(what: str, obj: str, data: dict) -> None:
        with db.tx() as con:
            audit.append(con, actor, f"assistant.memory.{what}", obj, {"role": r["role"], **data})

    if action == "list":
        return {"memory": {"items": await memory.items(ctx), "kinds": memory.KINDS}}
    if action == "search":
        return {"memory": {"hits": memory.search_history(ctx, str(query or ""))}}
    if action == "update":
        item = await memory.correct(ctx, str(item_id or ""), str(text or ""), kind or None)
        audited("update", item.id, {"kind": item.kind})
        return {"memory": {"item": memory.view(item)}}
    if action == "delete":
        n = int(await memory.forget(ctx, str(item_id or "")))
        if n:
            conv.scrub()
            audited("delete", str(item_id), {})
        return {"memory": {"deleted": n}}
    if action == "clear":
        n = await memory.forget_all(ctx)
        conv.scrub()
        audited("clear", "-", {"deleted": n})
        return {"memory": {"deleted": n}}
    if action == "materials":
        return {"memory": {"materials": knowledge.materials(ctx)}}
    if action == "material_add":
        try:
            raw = base64.b64decode(str(data or ""), validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("Tệp không đọc được") from None
        got = await knowledge.add_material(ctx, str(file_name or ""), raw)
        audited("material_add", got["key"], {"bytes": len(raw), "action": got["action"]})
        return {"memory": {"material": got}}
    if action == "material_delete":
        ok = await knowledge.delete_material(ctx, str(key or ""))
        if ok:
            audited("material_delete", str(key), {})
        return {"memory": {"deleted": int(ok)}}
    if action == "follow_ups":  # the person's follow-ups (A6): open, fired; what the bell shows
        from assistant import followups

        return {"memory": {"follow_ups": followups.listing(ctx), "unseen": followups.unseen(ctx)}}
    if action == "follow_up_cancel":
        from assistant import followups

        ok = followups.cancel(ctx, str(key or ""))
        if ok:
            audited("follow_up_cancel", str(key), {})
        return {"memory": {"cancelled": int(ok)}}
    if action == "follow_up_seen":
        from assistant import followups

        return {"memory": {"seen": int(followups.seen(ctx, str(key or "")))}}
    raise ValueError(
        "action là list, search, update, delete, clear, materials, material_add, material_delete, follow_ups, "
        "follow_up_cancel hoặc follow_up_seen"
    )


@op
async def retention_sweep() -> dict:
    """Compliance's retention: conversations past ``assistant_retention`` and expired items deleted (A4)."""
    from assistant.retention import sweep

    return {"swept": await sweep()}


@op
async def consolidate_due(tick: str = None, at: str = None) -> dict:
    """The memory consolidator's tick (A6): every conversation idle 15 minutes whose turns changed, distilled."""
    from assistant.consolidate import run_due

    return {"consolidated": await run_due()}


@op
def follow_ups_market(job: str = None, after: dict = None) -> dict:
    """After a market job: the open follow-ups on the series it loads, against their latest close (A6, no model)."""
    from assistant import followups

    return {"follow_ups": followups.check_market(followups.job_series(job) if job else None)}


@op
def follow_ups_topics(after: dict = None) -> dict:
    """After the news job: the open topic follow-ups against the events made effective since (A6, no model)."""
    from assistant import followups

    return {"follow_ups": followups.check_topics()}

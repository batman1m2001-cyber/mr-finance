"""The assistant's steps (A2): check → turn (operonx-agents, or the Copilot's path as the fallback) → answer."""

from __future__ import annotations

import time
from typing import Any, Dict, List

from operonx import op
from operonx.core.loggings import LOGGER

from assistant import registry
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
) -> dict:
    """Who asks (a customer always as client), what (≤ 2,000 characters), or which parked writes they answer."""
    role = auth.role_for(str(role or "client"))
    if role not in registry.DEMO_USER:
        raise roles.Forbidden(f"vai trò {role!r} không có")
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
            "message": message,
            "role": role,
            "client_id": client_id or None,
            "scope": scope or "personal",
            "route": str(route or ""),
            "followed": None if goals is None else [str(g) for g in goals][:50],
            "turn_id": str(turn_id or "") or None,
            "approvals": answers,
        }
    }


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


@op
async def turn(request: dict) -> dict:
    """One turn: the agent when a model is configured; else, or when the model fails before any tool ran, the
    fallback. A parked write is answered only by the person who asked, within ten minutes."""
    r = request
    if not turns.live():
        return {"result": await fallback(r, "chưa cấu hình mô hình cho trợ lý")}
    ctx = context(r)
    try:
        if r["approvals"]:
            return {"result": await turns.resume(ctx, r["turn_id"], r["approvals"])}
        got = await turns.run(ctx, r["message"])
        if got.get("model_error") and not ctx.trail:  # the model failed before any tool ran: NFR-03
            LOGGER.warning("assistant: the model failed (%s)", got["model_error"])
            return {"result": await fallback(r, f"mô hình lỗi ({got['model_error'].split(':')[0]})")}
        return {"result": got}
    except ValueError as exc:  # nothing waiting for this person, or too late
        return {"result": {"status": "failed", "mode": "model", "steps": [], "text": str(exc)}}
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
                }
            }
        return {"result": await fallback(r, f"mô hình lỗi ({type(exc).__name__})")}


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
    return {
        "assistant": {
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
    }

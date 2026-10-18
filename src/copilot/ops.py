"""The Copilot's steps: check → scrub → route → run (or ask to confirm) → answer."""

from __future__ import annotations

import time
from typing import Any, Dict

from operonx import op

from assistant.base import NotConfirmed, execute
from assistant.registry import plan as plan_of
from control import audit, db, roles
from copilot import router
from copilot.scrub import scrub
from copilot.tools import PAGES, TOOLS, USER, Ctx, ToolFailed, allowed
from people import auth

HELP = {
    "client": [
        "Tài sản của tôi thế nào?",
        "Dòng tiền tháng này?",
        "Có gì cần chú ý?",
        "Vì sao tin này ảnh hưởng tới tôi?",
        "Tạo kịch bản VN-Index giảm mạnh",
    ],
    "rm": [
        "Hôm nay cần gọi ai?",
        "Có gì cần chú ý với khách này?",
        "Điều tra tin lớn nhất",
        "Kịch bản lãi suất tăng",
        "Duyệt đề xuất đang chờ",
    ],
    "cio": [
        "Có gì chờ tôi duyệt?",
        "Phơi nhiễm lớn nhất ở đâu?",
        "Các agent chạy nền thế nào?",
        "Hộp tin có bao nhiêu tin?",
    ],
    "compliance": ["Có gì chờ Tuân thủ?", "Có bao nhiêu tin bị giữ?", "Chuỗi nhật ký còn nguyên không?"],
    # every role has its list: a role without one crashed the fallback (staff stress test D12)
    "specialist": ["Khuyến nghị nào đang chờ tôi duyệt?", "Chứng chỉ của tôi còn hiệu lực không?"],
    "admin": ["Hệ thống có gì bất thường?", "Chuỗi nhật ký còn nguyên không?", "Cấu hình nào chờ duyệt?"],
}


@op
def check_request(
    question: str = None,
    role: str = None,
    client_id: str = None,
    scope: str = None,
    route: str = None,
    confirm: dict = None,
    goals: list = None,
) -> dict:
    role = auth.role_for(str(role or "client"))
    if role not in USER:
        raise roles.Forbidden(f"vai trò {role!r} không có")
    question = str(question or "").strip()[:500]
    if not question and not confirm:
        raise ValueError("Hãy nhập câu hỏi")
    client_id = auth.client_for(client_id)  # as the assistant's requests; the tools' nested runs are checked too (D13)
    return {
        "question": question,
        "role": role,
        "client_id": client_id or None,
        "scope": scope or "personal",
        "route": str(route or ""),
        "confirm": confirm or None,
        "followed": None if goals is None else [str(g) for g in goals][:50],  # the goals followed in the browser
    }


@op
async def decide(question: str = "", role: str = "client", route: str = "", confirm: dict = None) -> dict:
    """Which tool: the confirmed one, or the router's choice on the scrubbed question."""
    seen = scrub(question)
    if confirm:
        return {
            "tool": confirm.get("tool"),
            "args": confirm.get("args") or {},
            "seen": seen,
            "router": {"kind": "confirm"},
            "confirmed": True,
        }
    if router.live():
        got = await router.llm(seen, route, role)
    else:
        got = {
            **router.keyword(seen, route, role),
            "router": {"kind": "keyword", "note": "bộ định tuyến từ khóa (mô phỏng)"},
        }
    return {**got, "seen": seen, "confirmed": False}


@op
async def act(
    tool: str = None,
    args: dict = None,
    confirmed: bool = False,
    role: str = "client",
    client_id: str = None,
    scope: str = "personal",
    question: str = "",
    followed: list = None,  # None does not bind across ops: the persona's defaults
) -> dict:
    """Run the tool, or for a write without confirm, describe it and stop. Failures are said as failures."""
    return {
        "result": await run_tool(tool, args or {}, bool(confirmed), role, client_id, scope, question or "", followed)
    }


async def run_tool(tool, args, confirmed, role, client_id, scope, question, followed=None) -> Dict[str, Any]:
    ctx = Ctx(
        role=role,
        client_id=client_id,
        scope=scope,
        question=question,
        followed=followed,
        user=auth.acting_id(USER.get(role)),
    )
    if not tool:
        return {
            "status": "unknown",
            "text": "Tôi chưa hiểu câu hỏi này. Tôi có thể giúp những việc dưới đây.",
            "suggest": HELP.get(role, []),
        }
    t = TOOLS.get(tool)
    if t is None:
        return {"status": "unknown", "text": "Không có công cụ này.", "suggest": HELP.get(role, [])}
    try:
        allowed(t, role)
        if t.write and not confirmed:
            plan = await plan_of(t, ctx, args)
            return {
                "status": "pending",
                "text": plan["summary"] + " Cần bạn xác nhận.",
                "confirm": {"tool": t.name, "args": plan["args"]},
                "tool": t.name,
            }
        if t.write:
            args = {k: v for k, v in args.items() if k in ("item_id", "decision")}
        out = await execute(t, ctx, args)  # within its timeout; a write read back after
    except roles.Forbidden as exc:
        return {"status": "forbidden", "text": str(exc), "tool": t.name, "suggest": HELP.get(role, [])}
    except NotConfirmed as exc:
        return {"status": "failed", "text": str(exc), "tool": t.name}
    except (ToolFailed, ValueError, KeyError) as exc:
        return {"status": "failed", "text": f"Không thực hiện được: {exc}", "tool": t.name}
    page = PAGES.get(t.page or "")
    link = page and page[1].get(role)
    return {
        "status": "ok",
        "text": out["text"],
        "tool": t.name,
        "navigate": out.get("navigate"),
        "evidence": link and {"label": page[0], "route": link},
        "focus": out.get("focus") or [],  # page elements the answer was read from (data-focus keys)
        "suggest": t.follow or HELP.get(role, []),
        "as_of": out.get("as_of"),  # the data's own date (prices, month), when the tool has one
        "sources": [x for x in out.get("sources") or [] if x],
        "card": out.get("card"),  # figures / list / bars / chain, drawn by the panel from the tool's numbers
    }


@op
def answer(result: dict, seen: str, router_info: dict, role: str = "client", client_id: str = None) -> dict:
    """The answer, stamped with its time and written to the audit chain: who asked (the demo user), which tool,
    what came of it, how it was routed and the question as the router saw it (scrubbed)."""
    at = time.time()
    actor = auth.acting_id(USER.get(role)) or f"client:{client_id or '-'}"
    with db.tx() as con:
        seq = audit.append(
            con,
            actor,
            "copilot.ask",
            result.get("tool") or "-",
            {
                "role": role,
                "client_id": client_id,
                "status": result.get("status"),
                "router": router_info.get("kind"),
                "model": router_info.get("model"),
                "seen": seen,
                "confirmed": router_info.get("kind") == "confirm",
            },
        )
    return {
        "copilot": {
            **result,
            "seen": seen,
            "router": router_info,
            "answered_at": at,
            "audit_seq": seq,
            "note": "Câu trả lời viết từ kết quả công cụ theo mẫu cố định; mô hình chỉ chọn công cụ.",
        }
    }

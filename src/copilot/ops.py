"""The Copilot's steps: check → scrub → route → run (or ask to confirm) → answer."""

from __future__ import annotations

from typing import Any, Dict

from operonx import op

from control import roles
from copilot import router
from copilot.scrub import scrub
from copilot.tools import PAGES, PLANS, TOOLS, USER, Ctx, ToolFailed, allowed

HELP = {
    "client": ["Tài sản của tôi thế nào?", "Dòng tiền tháng này?", "Có gì cần chú ý?", "Tin nào ảnh hưởng tới tôi?"],
    "rm": ["Hôm nay cần gọi ai?", "Có gì cần chú ý với khách này?", "Duyệt đề xuất đang chờ", "Mở đồ thị tác động"],
    "cio": ["Hộp tin có bao nhiêu tin?", "Lấy tin mới", "Mở hộp tin"],
    "compliance": ["Có bao nhiêu tin bị giữ?", "Mở tin bị giữ"],
}


@op
def check_request(
    question: str = None,
    role: str = None,
    client_id: str = None,
    scope: str = None,
    route: str = None,
    confirm: dict = None,
) -> dict:
    role = str(role or "client")
    if role not in USER:
        raise roles.Forbidden(f"vai trò {role!r} không có")
    question = str(question or "").strip()[:500]
    if not question and not confirm:
        raise ValueError("Hãy nhập câu hỏi")
    return {
        "question": question,
        "role": role,
        "client_id": client_id or None,
        "scope": scope or "personal",
        "route": str(route or ""),
        "confirm": confirm or None,
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
        got = {**router.keyword(seen, route), "router": {"kind": "keyword", "note": "bộ định tuyến từ khóa (mô phỏng)"}}
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
) -> dict:
    """Run the tool, or for a write without confirm, describe it and stop. Failures are said as failures."""
    return {"result": await run_tool(tool, args or {}, bool(confirmed), role, client_id, scope, question or "")}


async def run_tool(tool, args, confirmed, role, client_id, scope, question) -> Dict[str, Any]:
    ctx = Ctx(role=role, client_id=client_id, scope=scope, question=question)
    if not tool:
        return {
            "status": "unknown",
            "text": "Tôi chưa hiểu câu hỏi này. Tôi có thể giúp những việc dưới đây.",
            "suggest": HELP[role],
        }
    t = TOOLS.get(tool)
    if t is None:
        return {"status": "unknown", "text": "Không có công cụ này.", "suggest": HELP[role]}
    try:
        allowed(t, role)
        if t.write and not confirmed:
            plan = PLANS[t.name](ctx, args)
            return {
                "status": "pending",
                "text": plan["summary"] + " Cần bạn xác nhận.",
                "confirm": {"tool": t.name, "args": plan["args"]},
                "tool": t.name,
            }
        if t.write:
            args = {k: v for k, v in args.items() if k in ("item_id", "decision")}
        out = await t.run(ctx, args)
    except roles.Forbidden as exc:
        return {"status": "forbidden", "text": str(exc), "tool": t.name, "suggest": HELP[role]}
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
        "suggest": t.follow or HELP[role],
    }


@op
def answer(result: dict, seen: str, router_info: dict) -> dict:
    return {
        "copilot": {
            **result,
            "seen": seen,
            "router": router_info,
            "note": "Câu trả lời viết từ kết quả công cụ theo mẫu cố định; mô hình chỉ chọn công cụ.",
        }
    }

"""The assistant on ASSET_ALLOCATION_BRD and NEWS_EVIDENCE_BRD P2: the three buckets with the 11-class view, the
allocations waiting for the CIO with the RMs' bucket moves and the model's method, the event-type catalogue, and the
AI-suggested goal labels. Read-only: each reads what its page reads; a suggested label is kept only when the RM saves
it on Tác động tin."""

from __future__ import annotations

from typing import Any, Dict

from assistant.base import Ctx, Tool, ToolFailed, run_graph
from assistant.tools import USER, _family, _need_client, _pct, _vnd


async def buckets(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """Liquidity, Legacy, Growth: each gap, the return the retirement goal needs, and the 11-class view."""
    from allocation.graph import allocation_flow

    a = (await run_graph(allocation_flow, client_id=_need_client(ctx), scope=ctx.scope, role=ctx.role))["allocation"]
    liq, leg, ret, growth = a["liquidity"], a["legacy"], a["retirement"], a["growth"]
    legacy = f"thiếu {_vnd(leg['gap'])}–{_vnd(leg['gap_high'])}" if leg.get("gap") else "đủ"
    rows = sorted((r for r in a["eleven"]["rows"] if r["value"]), key=lambda r: -r["value"])
    eleven = "; ".join(
        f"{r['label']}{' (khoản vay)' if r['loan'] else ''} {_vnd(r['value'])}"
        + (f" (mục tiêu {_vnd(r['target'])})" if r["target"] is not None else "")
        for r in rows
    )
    text = (
        f"Thanh khoản: cần {_vnd(liq['target'])}, đang có {_vnd(liq['have'])}"
        + (f", thiếu {_vnd(liq['short'])}" if liq["short"] else "")
        + f". Di sản: {legacy}. Tăng trưởng: cần {_pct(ret['required'])}/năm cho mục tiêu hưu trí, mô hình kỳ vọng "
        f"{_pct(growth['expected'])}/năm. Theo 11 loại tài sản: {eleven or 'chưa có'}; ngoài 11 loại "
        f"{_vnd(a['eleven']['outside'])}."
    )
    if ctx.role != "client":  # the client sees only the actions the CIO approved (Q-29), on the page
        text += f" {len(a['actions'])} việc đề xuất; RM gửi CIO duyệt từng việc."
    return {
        "text": text,
        "data": {"liquidity_short": liq["short"], "legacy_gap": leg.get("gap") or 0, "required": ret["required"],
                 "expected": growth["expected"], "eleven": {r["key"]: r["value"] for r in rows}},  # fmt: skip
        "sources": ["Phân bổ tài sản (ba giỏ)", f"Mô hình: {a.get('method_label', '')}".strip(": ")],
    }


async def waiting(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The CIO's Phân bổ page: allocations waiting (each action's check), the method in force, the RMs' bucket moves."""
    from allocation import _model, ops

    q = ops.read_queue()
    method = _model.METHODS[ops.model_method()]
    each = "; ".join(
        f"{r['client_name']} ({r['id']}): {sum(x['status'] == 'pending' for x in r['data']['actions'])} việc chờ"
        for r in q["waiting"]
    )
    moves = "; ".join(
        f"{o['client_name']}: {o['name']} {o['from_label']} → {o['to_label']} ({o['reason'] or 'về giỏ mặc định'}, {o['by']})"
        for o in q["overrides"][:5]
    )
    return {
        "text": (f"{len(q['waiting'])} phân bổ chờ CIO duyệt: {each}." if q["waiting"] else "Không có phân bổ chờ duyệt.")
        + f" Mô hình đang dùng: {method}."
        + (f" RM chuyển giỏ gần đây: {moves}." if moves else " Chưa có lần RM chuyển giỏ.")
        + " Duyệt từng việc ở trang Phân bổ.",
        "data": {"waiting": len(q["waiting"]), "overrides": len(q["overrides"]), "method": ops.model_method()},
        "sources": ["Phân bổ (CIO)"],
    }


async def event_types(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The catalogue: each type, its precedents, and whether it reaches the statistics branch."""
    from evidence import catalogue as cat
    from evidence import frames

    dates = frames.events()
    types = {k: v for k, v in cat.event_types().items() if k != "new"}
    n = lambda k: len(dates.get(k, []))  # noqa: E731
    some = sorted((k for k in types if n(k)), key=lambda k: -n(k))
    each = "; ".join(f"{types[k]['label']}{' (CIO thêm)' if types[k].get('cio') else ''}: {n(k)} tiền lệ"
                     + (", đủ tiền lệ cho thống kê" if n(k) >= cat.MIN_PRECEDENTS else "") for k in some)
    rest = [types[k]["label"] for k in types if not n(k)]
    return {
        "text": f"{len(types)} loại sự kiện. Có tiền lệ: {each or 'chưa loại nào'}. {len(rest)} loại chưa có tiền lệ, đi "
        f"theo nhánh định tính ({', '.join(rest[:6])}{'…' if len(rest) > 6 else ''}). Từ {cat.MIN_PRECEDENTS} tiền lệ "
        f"và chênh từ {cat.MIN_EDGE * 100:g} điểm một loại có nhánh thống kê. CIO thêm loại hoặc ngày tiền lệ ở trang Bằng chứng tin.",
        "data": {k: n(k) for k in types},
        "sources": ["Danh mục loại sự kiện"],
    }


async def labels(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The AI's purpose and country for the family's goals the RM has not declared; nothing is kept."""
    from research.graph import goal_suggest_flow

    family = _family(ctx)
    got = await run_graph(goal_suggest_flow, family_id=family, by=ctx.user or USER["rm"])
    s = got["suggestions"]
    if got["mode"] == "none":
        return {"text": "Mọi mục tiêu của gia đình đã có nhãn (RM khai hoặc đọc được từ tên).", "data": {}}
    from datetime import date

    from procedural import goals
    from wealth import fixtures

    names = {g["goal_id"]: g["label"] for g in goals.goals_of(fixtures.client(family), date.today())}
    each = "; ".join(
        f"{names.get(k, k)}: " + (f"{x['purpose']} {x['country']}".strip() if x["purpose"] else "không chuyển ra nước ngoài")
        + (f" ({x['why']})" if x["why"] else "")
        for k, x in s.items()
    )
    if not each:
        raise ToolFailed("Agent không trả gợi ý nào")
    return {
        "text": f"Gợi ý của AI, chưa lưu: {each}. RM lưu ở trang Tác động tin (nút “Gợi ý bằng AI”).",
        "data": {"suggestions": s, "mode": got["mode"]},
        "sources": ["Gợi ý nhãn mục tiêu (AI)"],
    }


CATALOGUE: Dict[str, Tool] = {
    t.name: t
    for t in (
        Tool(
            "phan_bo_tai_san",
            "phân bổ ba giỏ của khách: Thanh khoản, Di sản, Tăng trưởng, phần thiếu, lợi nhuận cần cho mục tiêu hưu "
            "trí so với mô hình, và tài sản theo mười một loại",
            ("client", "rm"),
            buckets,
            page="phan-bo-tai-san",
            timeout=60.0,
        ),
        Tool(
            "phan_bo_cho_duyet",
            "các phân bổ RM gửi chờ CIO duyệt từng việc, cách tính mô hình đang dùng (nghiêng từng loại hay "
            "Black–Litterman) và các lần RM chuyển tài sản sang giỏ khác",
            ("cio",),
            waiting,
            page="phan-bo",
        ),
        Tool(
            "loai_su_kien",
            "danh mục loại sự kiện của bằng chứng tin: mỗi loại, số tiền lệ, loại nào đủ để có nhánh thống kê",
            ("cio",),
            event_types,
            page="bang-chung",
        ),
        Tool(
            "goi_y_nhan_muc_tieu",
            "AI gợi ý mục đích và quốc gia cho các mục tiêu của gia đình mà RM chưa khai; chỉ gợi ý, không lưu",
            ("rm",),
            labels,
            page="tac-dong",
            cost="llm",
            timeout=60.0,
        ),
    )
}

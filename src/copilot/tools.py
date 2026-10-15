"""The Copilot's tools (decision D3): each wraps a served graph or a role-filtered read the product already
has, so the server's role and separation-of-duty checks apply unchanged. A write never runs without the
user's confirm. Every answer is written here from the tool's result by a template: no model writes it."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional

from operonx import Operon

from apply import reads
from control import roles
from news import store as news_store
from wealth import store as wealth_store

USER = {"client": None, "rm": "rm01", "cio": "cio", "compliance": "compliance"}
PAGES = {  # page key → (label, route per role); the router may name a key, never a route
    "toan-canh": ("Toàn cảnh", {"client": "#/client/tong-quan/toan-canh", "rm": "#/rm/khach-hang/toan-canh"}),
    "chi-tiet": ("Chi tiết tài sản", {"client": "#/client/tong-quan/chi-tiet", "rm": "#/rm/khach-hang/tong-quan"}),
    "tai-san": ("Tài sản", {"client": "#/client/tai-san", "rm": "#/rm/khach-hang/tai-san"}),
    "ke-hoach": ("Kế hoạch", {"client": "#/client/muc-tieu/ke-hoach", "rm": "#/rm/khach-hang/ke-hoach"}),
    "tac-dong": ("Tác động tin", {"client": "#/client/tin/thi-truong", "rm": "#/rm/khach-hang/tac-dong"}),
    "do-thi": ("Đồ thị tác động", {"client": "#/client/tin/do-thi", "rm": "#/rm/khach-hang/do-thi"}),
    "duyet": ("Duyệt đề xuất", {"rm": "#/rm/khach-hang/duyet"}),
    "hom-nay": ("Hôm nay", {"rm": "#/rm/hom-nay"}),
    "hop-tin": ("Hộp tin", {"cio": "#/cio/hop-tin"}),
    "tin-bi-giu": ("Tin bị giữ", {"compliance": "#/compliance/giu"}),
}


class ToolFailed(RuntimeError):
    """The tool ran and did not succeed: said as such, never as a success."""


@dataclass
class Ctx:
    role: str
    client_id: Optional[str]
    scope: str
    question: str  # the original question: read only by our code (month parsing), never sent to a model


@dataclass
class Tool:
    name: str
    description: str  # what the router reads: no data, no digits
    roles: tuple
    run: Callable[[Ctx, Dict[str, Any]], Awaitable[Dict[str, Any]]]
    write: bool = False
    args: Dict[str, List[str]] = field(default_factory=dict)  # allowed router args: enumerations only
    page: Optional[str] = None
    follow: List[str] = field(default_factory=list)


def _vnd(x: float, signed: bool = False) -> str:
    a = abs(x)
    s = f"{a / 1e9:.2f} tỷ" if a >= 1e9 else f"{a / 1e6:.1f} triệu"
    s = s.replace(".", ",")
    return (("+" if x > 0 else "−" if x < 0 else "") if signed else ("−" if x < 0 else "")) + s


def _pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%".replace(".", ",")


async def _graph(graph, **inputs) -> Dict[str, Any]:
    out = await Operon(graph, params={k: None for k in inputs}).run(inputs=inputs)
    if "$errors" in out:
        err = next(iter(out["$errors"].values()))
        raise ToolFailed(str(err.get("message") or err.get("type") or err))
    return out


def _need_client(ctx: Ctx) -> str:
    if not ctx.client_id:
        raise ToolFailed("Chưa chọn khách hàng")
    return ctx.client_id


def _family(ctx: Ctx) -> str:
    from wealth import fixtures

    cid = _need_client(ctx)
    return fixtures.client(cid).get("member_of") or cid


# -- read tools --------------------------------------------------------------------------------


async def overview(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from dashboard.graph import dashboard_flow

    d = (await _graph(dashboard_flow, client_id=_need_client(ctx), scope=ctx.scope))["dashboard"]
    nw, lq, rk = d["net_worth"], d["liquidity"], d["risk"]
    status = {"ok": "an toàn", "near": "gần ngưỡng", "over": "vượt ngưỡng"}[rk["status"]]
    months = f"{lq['months'] / 12:.0f} năm" if lq["months"] >= 24 else f"{lq['months']:.0f} tháng"
    text = (
        f"Tài sản ròng {_vnd(nw['value'])} ({_vnd(nw['month_change'], True)}, {_pct(nw['month_change_pct'])} so với "
        f"tháng trước). Thanh khoản dự phòng {_vnd(lq['value'])}, đủ chi {months}. Khi thị trường xấu, mức sụt giảm "
        f"ước tính {_pct(rk['current'])} so với ngưỡng {_pct(rk['limit'], 0)}: {status}."
    )
    return {
        "text": text,
        "data": {"net_worth": nw["value"], "risk": rk["status"], "as_of": d["as_of"]},
        "focus": ["kpi:net_worth", "kpi:liquidity", "kpi:risk"],
    }


MONTH = re.compile(r"(?:tháng|t)\s*(\d{1,2})(?:\s*[/\-]\s*(\d{2,4}))?", re.I)


async def money_flow(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from flows.graph import flows_flow

    month = None
    m = MONTH.search(ctx.question or "")  # parsed here, from the original question; the router never sees it
    first = (await _graph(flows_flow, client_id=_need_client(ctx), scope=ctx.scope, month=None))["flows"]
    if m:
        mm = int(m.group(1))
        yy = m.group(2)
        cands = [x for x in first["months"] if int(x[5:]) == mm and (not yy or x[:4].endswith(yy[-2:]))]
        month = cands[-1] if cands else None
        if not cands:
            raise ToolFailed(f"Không có giao dịch trong tháng {mm}{'/' + yy if yy else ''}")
    f = (
        first
        if not month or month == first["month"]
        else (await _graph(flows_flow, client_id=ctx.client_id, scope=ctx.scope, month=month))["flows"]
    )
    top = f["outflow"][0] if f["outflow"] else None
    left = "còn lại" if f["left"] >= 0 else "thiếu hụt"
    text = (
        f"Tháng {f['month'][5:]}/{f['month'][:4]}: tiền vào {_vnd(f['total_in'])}, tiền ra {_vnd(f['total_out'])}, "
        f"{left} {_vnd(abs(f['left']))}."
        + (f" Khoản chi lớn nhất: {top['label']} {_vnd(top['amount'])} ({len(top['rows'])} giao dịch)." if top else "")
    )
    focus = [f"flow:{f['month']}"] + ([f"flow:{f['month']}:out:{top['category']}"] if top else [])
    return {"text": text, "data": {"month": f["month"], "left": f["left"]}, "focus": focus}


async def watch(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from feed.graph import feed_flow

    role = "rm" if ctx.role == "rm" else "client"
    items = (await _graph(feed_flow, client_id=_need_client(ctx), scope=ctx.scope, role=role))["feed"]["items"]
    if not items:
        return {"text": "Không có điều gì cần chú ý lúc này.", "data": {"items": 0}}
    lines = [f"{k + 1}) {i['title']} — {i['why']}." for k, i in enumerate(items[:3])]
    more = f" Còn {len(items) - 3} mục khác trên Toàn cảnh." if len(items) > 3 else ""
    return {
        "text": f"{len(items)} điều đáng chú ý. " + " ".join(lines) + more,
        "data": {"items": len(items)},
        "focus": [i["key"] for i in items[:3]],
    }


async def goals(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from scenarios.graph import goals_flow

    out = (await _graph(goals_flow, client_id=_need_client(ctx), scope=ctx.scope))["goals"]
    followed = [g for g in out if g["followed"]]
    label = {"on_track": "đúng tiến độ", "at_risk": "cần chú ý", "off_track": "chậm tiến độ"}
    lines = [f"{g['title']}: {label.get(g['goal']['status'], g['goal']['status'])}" for g in followed]
    text = (
        f"{len(followed)} mục tiêu đang theo dõi. " + "; ".join(lines) + "."
        if followed
        else "Chưa có mục tiêu đang theo dõi."
    )
    return {"text": text, "data": {"followed": len(followed)}}


async def impact(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    role = "rm" if ctx.role == "rm" else "client"
    d = reads.family_impact(_family(ctx), role)
    eff = [i for i in d["items"] if i["status"] == "EFFECTIVE"]
    if not eff:
        return {"text": "Chưa có tin nào được CIO duyệt áp dụng cho gia đình này.", "data": {"events": 0}}
    big = max(eff, key=lambda i: abs(i["horizons"]["3m"]["expected"]))
    text = (
        f"{len(eff)} sự kiện đang có hiệu lực; tác động kỳ vọng 3 tháng cộng lại "
        f"{_vnd(d['effective_expected_3m'], True)}. "
        f"Lớn nhất: {big['event']['title']} ({_vnd(big['horizons']['3m']['expected'], True)}). Đây là ước tính theo "
        "kịch bản CIO duyệt, không phải khuyến nghị."
    )
    return {"text": text, "data": {"events": len(eff)}, "focus": [f"event:{big['event']['id']}"]}


async def rm_today(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    d = reads.rm_today()
    fams = sorted({c["family_id"] for c in d["cases"]})
    tasks = d.get("goal_tasks") or d.get("tasks") or []
    text = (
        f"{len(fams)} gia đình cần xem trước (P10 3 tháng ≤ −5% tài sản ròng)."
        if fams
        else "Không có gia đình nào chạm ngưỡng xem trước."
    ) + (f" {len(tasks)} việc theo mục tiêu." if tasks else "")
    return {"text": text, "data": {"families": len(fams)}, "focus": [f"family:{f}" for f in fams]}


async def inbox(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    items = news_store.inbox()
    return {"text": f"Hộp tin có {len(items)} tin mới đã qua cổng lọc.", "data": {"items": len(items)}}


async def held(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    items = [i for i in news_store.inbox() if i.get("held")]
    return {"text": f"{len(items)} tin đang bị giữ vì nhắc tên trong danh sách hạn chế.", "data": {"items": len(items)}}


async def navigate(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    page = args.get("page")
    if page not in PAGES or ctx.role not in PAGES[page][1]:
        raise ToolFailed("Không có trang này cho vai trò hiện tại")
    label, routes = PAGES[page]
    return {"text": f"Mở trang {label}.", "navigate": routes[ctx.role], "data": {"page": page}}


# -- write tools (confirm first) ---------------------------------------------------------------


def _pending_review(ctx: Ctx) -> Dict[str, Any]:
    cid = _need_client(ctx)
    waiting = [r for r in wealth_store.reviews() if r["status"] == "pending" and r["client_id"] == cid]
    if not waiting:
        raise ToolFailed("Không có đề xuất nào đang chờ duyệt cho khách hàng này")
    if len(waiting) > 1:
        raise ToolFailed(f"Có {len(waiting)} đề xuất đang chờ: mở trang Duyệt đề xuất để chọn từng đề xuất")
    return waiting[0]


def plan_review(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    item = _pending_review(ctx)
    decision = args.get("decision") if args.get("decision") in ("approved", "rejected") else "approved"
    verb = "Duyệt" if decision == "approved" else "Từ chối"
    return {
        "summary": f"{verb} đề xuất “{item['title']}”?",
        "args": {"item_id": item["id"], "decision": decision},
    }


async def review(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from review.graph import review_flow

    out = await _graph(
        review_flow, item_id=args.get("item_id"), decision=args.get("decision"), note="Qua Copilot", by=USER[ctx.role]
    )
    it = out["item"]
    return {
        "text": f"Đã ghi: {'duyệt' if it['status'] == 'approved' else 'từ chối'} “{it['title']}”.",
        "data": {"id": it["id"]},
    }


def plan_fetch(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    return {"summary": "Lấy tin mới ngay từ các nguồn trong danh sách trắng?", "args": {}}


async def fetch(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from news.graph import ingest_flow

    s = (await _graph(ingest_flow, feeds=None, now=None, tick=None, at=None))["ingest"]
    return {
        "text": f"Đã lấy tin: thêm {s['added']}, bỏ {s['refused']}, trùng {s['duplicates']}, giữ {s['held']}.",
        "data": s,
    }


TOOLS: Dict[str, Tool] = {
    t.name: t
    for t in [
        Tool(
            "tong_quan",
            "tài sản ròng, thay đổi trong tháng, thanh khoản dự phòng, mức rủi ro so với ngưỡng",
            ("client", "rm"),
            overview,
            page="toan-canh",
            follow=["Có gì cần chú ý?", "Dòng tiền tháng này?"],
        ),
        Tool(
            "dong_tien",
            "tiền vào, tiền ra, còn lại trong một tháng, khoản chi lớn nhất",
            ("client", "rm"),
            money_flow,
            page="toan-canh",
            follow=["Có gì cần chú ý?", "Mục tiêu của tôi thế nào?"],
        ),
        Tool(
            "chu_y",
            "những điều đáng chú ý lúc này và vì sao",
            ("client", "rm"),
            watch,
            page="toan-canh",
            follow=["Tin nào ảnh hưởng tới tôi?", "Tổng quan tài sản?"],
        ),
        Tool(
            "muc_tieu",
            "các mục tiêu đang theo dõi và tiến độ",
            ("client", "rm"),
            goals,
            page="ke-hoach",
            follow=["Có gì cần chú ý?"],
        ),
        Tool(
            "tac_dong",
            "tác động của tin đã được CIO duyệt lên tài sản gia đình",
            ("client", "rm"),
            impact,
            page="tac-dong",
            follow=["Mở đồ thị tác động", "Có gì cần chú ý?"],
        ),
        Tool(
            "hom_nay",
            "các gia đình RM cần xem trước hôm nay",
            ("rm",),
            rm_today,
            page="hom-nay",
            follow=["Có gì cần chú ý?"],
        ),
        Tool("hop_tin", "số tin mới trong hộp tin của CIO", ("cio",), inbox, page="hop-tin", follow=["Lấy tin mới"]),
        Tool("tin_bi_giu", "số tin bị giữ vì danh sách hạn chế", ("compliance",), held, page="tin-bi-giu"),
        Tool(
            "mo_trang",
            "mở một trang của ứng dụng",
            ("client", "rm", "cio", "compliance"),
            navigate,
            args={"page": list(PAGES)},
        ),
        Tool(
            "duyet_de_xuat",
            "duyệt hoặc từ chối đề xuất đang chờ của khách hàng đang chọn",
            ("rm",),
            review,
            write=True,
            args={"decision": ["approved", "rejected"]},
            page="duyet",
        ),
        Tool("lay_tin", "lấy tin mới ngay từ các nguồn", ("cio",), fetch, write=True, page="hop-tin"),
    ]
}
PLANS = {"duyet_de_xuat": plan_review, "lay_tin": plan_fetch}


def allowed(tool: Tool, role: str) -> None:
    if role not in tool.roles:
        names = ", ".join(roles.ROLE_LABELS[r] for r in tool.roles)
        raise roles.Forbidden(f"Vai trò {roles.ROLE_LABELS.get(role, role)} không dùng được việc này; cần: {names}")

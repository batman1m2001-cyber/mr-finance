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
from people import auth
from wealth import store as wealth_store

USER = {"client": None, "rm": "rm01", "cio": "cio", "compliance": "compliance"}
PAGES = {  # page key → (label, route per role); the router may name a key, never a route
    "toan-canh": ("Toàn cảnh", {"client": "#/client/tong-quan/toan-canh", "rm": "#/rm/khach-hang/toan-canh"}),
    "ban-do": ("Bản đồ tài chính", {"client": "#/client/tong-quan/ban-do", "rm": "#/rm/khach-hang/ban-do"}),
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
    followed: Optional[List[str]] = None  # goal ids the client follows in this browser (None: the persona's)


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
    tone = {"ok": "good", "near": "warn", "over": "bad"}[rk["status"]]
    used = [s for s in d["sources"] if s["count"]]
    return {
        "text": text,
        "data": {"net_worth": nw["value"], "risk": rk["status"], "as_of": d["as_of"]},
        "focus": ["kpi:net_worth", "kpi:liquidity", "kpi:risk"],
        "as_of": d["as_of"],
        "sources": [f"Tổng hợp {sum(s['count'] for s in used)} khoản từ {len(used)} nguồn"],
        "card": {
            "kind": "figures",
            "items": [
                {
                    "label": "Tài sản ròng",
                    "value": _vnd(nw["value"]),
                    "sub": f"{_vnd(nw['month_change'], True)} tháng này",
                    "tone": "good" if nw["month_change"] >= 0 else "bad",
                },
                {"label": "Thanh khoản dự phòng", "value": _vnd(lq["value"]), "sub": f"đủ chi {months}"},
                {
                    "label": "Sụt giảm khi thị trường xấu",
                    "value": _pct(rk["current"]),
                    "sub": f"ngưỡng {_pct(rk['limit'], 0)} · {status}",
                    "tone": tone,
                },
            ],
        },
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
    return {
        "text": text,
        "data": {"month": f["month"], "left": f["left"]},
        "focus": focus,
        "as_of": f["month"],
        "sources": [f"{sum(len(x['rows']) for x in f['inflow'] + f['outflow'])} giao dịch của tháng"],
        "card": {
            "kind": "bars",
            "title": "Chi lớn nhất trong tháng",
            "items": [{"label": x["label"], "value": x["amount"], "text": _vnd(x["amount"])} for x in f["outflow"][:5]],
            "figures": [
                {"label": "Vào", "value": _vnd(f["total_in"]), "tone": "good"},
                {"label": "Ra", "value": _vnd(f["total_out"]), "tone": "bad"},
                {
                    "label": left.capitalize(),
                    "value": _vnd(abs(f["left"])),
                    "tone": "good" if f["left"] >= 0 else "bad",
                },
            ],
        },
    }


async def watch(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from feed.graph import feed_flow

    role = "rm" if ctx.role == "rm" else "client"
    items = (await _graph(feed_flow, client_id=_need_client(ctx), scope=ctx.scope, role=role))["feed"]["items"]
    if not items:
        return {"text": "Không có điều gì cần chú ý lúc này.", "data": {"items": 0}}
    lines = [f"{k + 1}) {i['title']} — {i['why']}." for k, i in enumerate(items[:3])]
    more = f" Còn {len(items) - 3} mục khác trên Toàn cảnh." if len(items) > 3 else ""
    level = {"high": ("bad", "Cao"), "medium": ("warn", "Vừa"), "info": ("", "Thông tin")}
    return {
        "text": f"{len(items)} điều đáng chú ý. " + " ".join(lines) + more,
        "data": {"items": len(items)},
        "focus": [i["key"] for i in items[:3]],
        "sources": ["Bảng tin: ngưỡng của sản phẩm trên số liệu tổng hợp, giao dịch và tin đã duyệt"],
        "card": {
            "kind": "list",
            "items": [
                {
                    "title": i["title"],
                    "sub": i["why"],
                    "chip": level.get(i.get("severity"), ("", ""))[1],
                    "tone": level.get(i.get("severity"), ("", ""))[0],
                    "focus": i["key"],
                }
                for i in items[:5]
            ],
        },
    }


async def goals(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from scenarios.graph import goals_flow

    out = (await _graph(goals_flow, client_id=_need_client(ctx), scope=ctx.scope))["goals"]
    followed = [g for g in out if (g["id"] in ctx.followed if ctx.followed is not None else g["followed"])]
    label = {"on_track": "đúng tiến độ", "at_risk": "cần chú ý", "off_track": "chậm tiến độ"}
    lines = [f"{g['title']}: {label.get(g['goal']['status'], g['goal']['status'])}" for g in followed]
    text = (
        f"{len(followed)} mục tiêu đang theo dõi. " + "; ".join(lines) + "."
        if followed
        else "Chưa có mục tiêu đang theo dõi."
    )
    tone = {"on_track": "good", "at_risk": "warn", "off_track": "bad"}
    return {
        "text": text,
        "data": {"followed": len(followed)},
        "sources": ["Mục tiêu theo hồ sơ khách hàng, tính trên tài sản hiện có"],
        "card": {
            "kind": "list",
            "items": [
                {
                    "title": g["title"],
                    "sub": f"cần {_vnd(g['goal']['need'])} · có {_vnd(g['goal']['have'])}",
                    "chip": label.get(g["goal"]["status"], ""),
                    "tone": tone.get(g["goal"]["status"], ""),
                    "progress": max(0.0, min(1.0, g["goal"].get("progress") or 0.0)),
                    "focus": f"goal:{g['id']}",
                }
                for g in followed
            ],
        },
    }


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
    return {
        "text": text,
        "data": {"events": len(eff)},
        "focus": [f"event:{big['event']['id']}"],
        "as_of": big.get("price_date"),
        "sources": [
            f"{len(eff)} lần áp dụng CIO duyệt",
            *sorted({o for i in eff for o in i["sources"]["outlets"]})[:3],
        ],
        "card": {
            "kind": "list",
            "items": [
                {
                    "title": i["event"]["title"],
                    "sub": "kỳ vọng 3 tháng",
                    "value": _vnd(i["horizons"]["3m"]["expected"], True),
                    "tone": "bad" if i["horizons"]["3m"]["expected"] < 0 else "good",
                    "focus": f"event:{i['event']['id']}",
                }
                for i in sorted(eff, key=lambda i: -abs(i["horizons"]["3m"]["expected"]))[:5]
            ],
        },
    }


STRESS = {  # what the router may choose (plain words: it never sees a digit) → a stress scenario of scenarios._sim
    "co_phieu": "vni_30",
    "trai_phieu": "bond_crisis",
    "bat_dong_san": "re_freeze",
    "lai_suat": "rates_up",
    "ty_gia": "usd_up",
}


async def investigate(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """An approved event's path to the family, read from the impact graph (the largest by 3-month effect)."""
    from apply.impact_graph import family_graph

    g = family_graph(_family(ctx), "rm" if ctx.role == "rm" else "client")
    events = [n for n in g["nodes"] if n["kind"] == "event"]
    if not events:
        raise ToolFailed("Chưa có tin nào được CIO duyệt áp dụng cho gia đình này")
    ev = max(events, key=lambda n: abs(n.get("expected_3m") or 0))
    by = {n["id"]: n for n in g["nodes"]}
    down = lambda ids: {e["to"] for e in g["edges"] if e["from"] in ids}  # noqa: E731
    branches = sorted((by[i] for i in down({ev["id"]})), key=lambda n: -n.get("probability", 0))
    factors = sorted(
        (by[i] for i in down({b["id"] for b in branches}) if i in by), key=lambda n: -abs(n.get("contribution") or 0)
    )
    run = ev.get("run")
    assets = sorted(
        (
            (by[e["from"]], e["by_run"][run])
            for e in g["edges"]
            if e["to"].startswith("FAM:") and run in (e.get("by_run") or {})
        ),
        key=lambda x: -abs(x[1]),
    )
    goals = [n for n in g["nodes"] if n["kind"] == "goal"]
    news = [
        n
        for n in g["nodes"]
        if n["kind"] == "news" and any(e["from"] == n["id"] and e["to"] == ev["id"] for e in g["edges"])
    ]
    main = branches[0] if branches else None
    text = (
        f"{ev['label']}: {len(news)} tin, CIO duyệt {len(branches)} kịch bản"
        + (f" (chính: {main['label']})" if main else "")
        + (f"; đi qua {', '.join(f['label'] for f in factors[:2])}" if factors else "")
        + (f"; tới {', '.join(a['label'] for a, _ in assets[:3])}" if assets else "")
        + f". Tác động kỳ vọng 3 tháng {_vnd(ev.get('expected_3m') or 0, True)}. Có thể ảnh hưởng theo kịch bản, "
        "không phải quan hệ nhân quả."
    )
    return {
        "text": text,
        "data": {"event": ev["ref"], "run": run, "factors": len(factors), "assets": len(assets)},
        "focus": [f"event:{ev['ref']}"],
        "sources": [
            f"Lần áp dụng {run}",
            f"Nhận định {main['ref']}" if main else "",
            *sorted({n.get("outlet") or n["label"].split(" · ")[0] for n in news})[:2],
        ],
        "card": {
            "kind": "chain",
            "steps": [
                {"label": "Tin", "items": [n["label"] for n in news[:2]]},
                {"label": "Sự kiện", "items": [ev["label"]]},
                {"label": "Kịch bản", "items": [b["label"] for b in branches[:3]]},
                {"label": "Yếu tố", "items": [f["label"] for f in factors[:3]]},
                {"label": "Tài sản", "items": [f"{a['label']} {_vnd(v, True)}" for a, v in assets[:3]]},
                *(
                    [{"label": "Mục tiêu", "items": [f"{x['label']}: {x['before']} → {x['after']}" for x in goals[:2]]}]
                    if goals
                    else []
                ),
            ],
        },
    }


async def stress(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """One stress test on the client's own holdings, through the planning page's scenario_flow."""
    from scenarios.graph import scenario_flow

    sid = STRESS.get(args.get("scenario"), "vni_30")
    r = (await _graph(scenario_flow, client_id=_need_client(ctx), scenario=sid, params=None, scope=ctx.scope))["result"]
    b, a = r["before"], r["after"]
    d = a["net_worth"] - b["net_worth"]
    pct = d / b["net_worth"] if b["net_worth"] else 0.0
    verdict = next((x["value"] for x in r["summary"] if x["label"].startswith("So với ngưỡng")), "")
    text = (
        f"Kịch bản {r['title']}: tài sản ròng {_vnd(b['net_worth'])} → {_vnd(a['net_worth'])} ({_vnd(d, True)}, "
        f"{'−' if pct < 0 else '+'}{_pct(abs(pct))})"
        + (f"; so với ngưỡng chấp nhận: {verdict}" if verdict else "")
        + ". Đây là mô phỏng trên tài sản hiện có, không phải dự báo."
    )
    return {
        "text": text,
        "data": {"scenario": sid, "before": b["net_worth"], "after": a["net_worth"]},
        "as_of": r.get("as_of"),
        "sources": ["Mô phỏng kịch bản trên các khoản hiện có (trang Kế hoạch)"],
        "card": {
            "kind": "figures",
            "title": r["title"],
            "items": [
                {"label": "Trước", "value": _vnd(b["net_worth"])},
                {
                    "label": "Sau cú sốc",
                    "value": _vnd(a["net_worth"]),
                    "sub": f"{_vnd(d, True)} · {'−' if pct < 0 else '+'}{_pct(abs(pct))}",
                    "tone": "bad" if d < 0 else "good",
                },
                {
                    "label": "Thanh khoản sau",
                    "value": _vnd(a["liquid"]),
                    "sub": f"{a['liquid_months']:.0f} tháng chi tiêu".replace(".", ","),
                },
            ],
            "notes": [f"{x['label']}: {x['value']}" for x in r["summary"] if x["label"].startswith("Ảnh hưởng nhiều")][
                :3
            ],
        },
    }


async def rm_today(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    d = reads.rm_today()
    fams = sorted({c["family_id"] for c in d["cases"]})
    tasks = d.get("goal_tasks") or d.get("tasks") or []
    text = (
        f"{len(fams)} gia đình cần xem trước (P10 3 tháng ≤ −5% tài sản ròng)."
        if fams
        else "Không có gia đình nào chạm ngưỡng xem trước."
    ) + (f" {len(tasks)} việc theo mục tiêu." if tasks else "")
    return {
        "text": text,
        "data": {"families": len(fams)},
        "focus": [f"family:{f}" for f in fams],
        "sources": ["Hậu kiểm của các lần áp dụng đang hiệu lực"],
        "card": {
            "kind": "list",
            "items": [  # the worst case of each family first (the list is sorted worst first)
                {
                    "title": c.get("name") or c["family_id"],
                    "sub": f"P10 3 tháng {_pct(c['p10_3m_pct'])} tài sản ròng · {c['event']['title']}",
                    "chip": "Xem trước",
                    "tone": "bad",
                    "focus": f"family:{c['family_id']}",
                }
                for c in sorted(
                    {c["family_id"]: c for c in reversed(d["cases"])}.values(), key=lambda c: c["p10_3m_pct"]
                )
            ],
        },
    }


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
        review_flow,
        item_id=args.get("item_id"),
        decision=args.get("decision"),
        note="Qua Copilot",
        by=auth.acting_id(USER[ctx.role]),
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
            follow=["Vì sao tin này ảnh hưởng tới tôi?", "Tạo kịch bản VN-Index giảm mạnh", "Mở đồ thị tác động"],
        ),
        Tool(
            "dieu_tra",
            "điều tra đường đi của tin đã duyệt: tin, kịch bản, yếu tố, tài sản, mục tiêu",
            ("client", "rm"),
            investigate,
            page="do-thi",
            follow=["Tạo kịch bản VN-Index giảm mạnh", "Tin nào ảnh hưởng tới tôi?"],
        ),
        Tool(
            "kich_ban",
            "chạy một kịch bản sốc thị trường trên tài sản hiện có",
            ("client", "rm"),
            stress,
            args={"scenario": list(STRESS)},
            page="ke-hoach",
            follow=["Kịch bản lãi suất tăng", "Kịch bản bất động sản đóng băng", "Mục tiêu của tôi thế nào?"],
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

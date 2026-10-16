"""The app's served graphs as assistant tools (A1, ADR-0032): reads beyond the Copilot's, and the writes a person
may ask for in a sentence. Each runs the graph the page posts to, as the person, so the server's role, family
and separation-of-duty checks apply unchanged; a write is planned (the line the person confirms, its arguments
resolved here), then read back by its verifier.

Left to their pages, deliberately: the four-eyes governance decisions (configuration versions, CIO views and
runs, newsletters, policy documents, research release, the market model), grouping news into events, releasing
held news and the client's own uploads and risk test. Each needs the person to read evidence on that page; the
assistant opens the page (``mo_trang``) instead of acting."""

from __future__ import annotations

from typing import Any, Dict, List

from assistant.base import Ctx, Param, Tool, ToolFailed
from assistant.tools import STRESS, _family, _graph, _need_client, _vnd
from wealth import fixtures
from wealth import store as wealth_store

STAFF = ("rm", "cio", "compliance", "admin", "specialist")
STATUS = {
    "pending": "chờ RM duyệt",
    "pending_specialist": "chờ chuyên gia duyệt",
    "approved": "đã duyệt",
    "rejected": "đã từ chối",
}


def _name(client_id: str) -> str:
    return fixtures.client(client_id).get("name") or client_id


def _review(item_id: str) -> Dict[str, Any]:
    it = wealth_store.review(str(item_id or ""))
    if it is None:
        raise ToolFailed(f"Không có đề xuất {item_id}")
    return it


# -- reads -------------------------------------------------------------------------------------


async def drivers(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """What is moving the client's wealth: each policy, macro move and project, in VND (the policy-cost page)."""
    from impact.graph import alerts_flow

    r = (await _graph(alerts_flow, client_id=_need_client(ctx), scope=ctx.scope))["report"]
    found = sorted(r["alerts"], key=lambda a: -abs(a["impact"]))
    if not found:
        return {"text": "Chưa thấy chính sách, biến động vĩ mô hay dự án nào tác động tới tài sản.", "data": {"n": 0}}
    top = found[0]
    text = (
        f"{len(found)} yếu tố đang tác động: {r['risks']} rủi ro, {r['opportunities']} cơ hội; tổng ước tính "
        f"{_vnd(r['total_impact'], True)}. Lớn nhất: {top['title']} — {top['message']}"
    )
    return {
        "text": text,
        "data": {"n": len(found), "total_impact": r["total_impact"], "as_of": r["as_of"]},
        "as_of": r["as_of"],
        "sources": sorted({a["source"] for a in found[:3] if a.get("source")}),
        "card": {
            "kind": "list",
            "items": [
                {
                    "title": a["title"],
                    "sub": f"{_vnd(a['impact'], True)} · {a['status_label']}",
                    "chip": a["severity_label"],
                    "tone": "good" if a["opportunity"] else "bad" if a["severity"] == "high" else "warn",
                }
                for a in found[:5]
            ],
        },
    }


async def search(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The header's search: what the role may open, each hit with its page."""
    from search.graph import search_flow

    q = str(args.get("q") or "").strip()[:100]
    if not q:
        raise ToolFailed("Cần từ khóa để tìm")
    hits = (await _graph(search_flow, q=q, role=ctx.role, client_id=ctx.client_id, scope=ctx.scope))["search"]["hits"]
    if not hits:
        return {"text": f"Không tìm thấy gì cho “{q}” trong những gì bạn được xem.", "data": {"hits": 0}}
    return {
        "text": f"{len(hits)} kết quả cho “{q}”: " + "; ".join(h["label"] for h in hits[:5]) + ".",
        "data": {"hits": len(hits), "items": [{"label": h["label"], "route": h["route"]} for h in hits[:10]]},
        "card": {
            "kind": "list",
            "items": [{"title": h["label"], "sub": h.get("sub") or "", "route": h["route"]} for h in hits[:8]],
        },
    }


async def queue(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The proposals and recommendations in the queue: the selected client's (client, RM), or those waiting for this
    specialist."""
    from people import auth

    if ctx.role == "specialist":
        items = [r for r in wealth_store.reviews(status="pending_specialist") if auth.visible([r["client_id"]])]
    else:
        items = wealth_store.reviews(client_id=_need_client(ctx))
    if not items:
        return {"text": "Không có đề xuất nào trong hàng chờ.", "data": {"items": []}}
    waiting = [r for r in items if r["status"] in ("pending", "pending_specialist")]
    text = f"{len(items)} đề xuất, {len(waiting)} đang chờ. " + " ".join(
        f"{k + 1}) {r['title']} — {STATUS.get(r['status'], r['status'])}." for k, r in enumerate(items[:4])
    )
    return {
        "text": text,
        "data": {"items": [{"id": r["id"], "title": r["title"], "status": r["status"]} for r in items[:20]]},
        "focus": [f"review:{r['id']}" for r in waiting[:5]],
        "card": {
            "kind": "list",
            "items": [
                {
                    "title": r["title"],
                    "sub": f"{_name(r['client_id'])} · {STATUS.get(r['status'], r['status'])}",
                    "chip": r["id"],
                    "tone": "warn" if r in waiting else "",
                    "focus": f"review:{r['id']}",
                }
                for r in items[:6]
            ],
        },
    }


async def events(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The CIO's events, newest first: urgent or not, held by Compliance or not."""
    from events import store as events_store

    evs = events_store.listing()
    if not evs:
        return {"text": "Chưa có sự kiện nào.", "data": {"events": []}}
    urgent = [e for e in evs if e.get("urgent")]
    text = f"{len(evs)} sự kiện, {len(urgent)} đang đánh dấu khẩn. " + " ".join(
        f"{k + 1}) {e['title']}{' (khẩn)' if e.get('urgent') else ''}{' (bị giữ)' if e['blocked'] else ''}."
        for k, e in enumerate(evs[:4])
    )
    return {
        "text": text,
        "data": {
            "events": [
                {"id": e["id"], "title": e["title"], "urgent": bool(e.get("urgent")), "held": e["blocked"]}
                for e in evs[:20]
            ]
        },
        "card": {
            "kind": "list",
            "items": [
                {
                    "title": e["title"],
                    "sub": f"{len(e['news_ids'])} tin" + (" · bị giữ" if e["blocked"] else ""),
                    "chip": "Khẩn" if e.get("urgent") else e["id"],
                    "tone": "bad" if e.get("urgent") else "",
                }
                for e in evs[:6]
            ],
        },
    }


async def system_alerts(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The bell's alerts for this role (NFR-12): open or acknowledged, not yet resolved."""
    from control import alerts

    found = alerts.for_role(ctx.role)
    if not found:
        return {"text": "Không có cảnh báo hệ thống nào.", "data": {"alerts": []}}
    opened = [a for a in found if a["status"] == "open"]
    text = f"{len(found)} cảnh báo hệ thống, {len(opened)} chưa ai xem. " + " ".join(
        f"{k + 1}) {a['label']}: {a['title']}." for k, a in enumerate(found[:3])
    )
    return {
        "text": text,
        "data": {"alerts": [{"id": a["id"], "title": a["title"], "status": a["status"]} for a in found[:20]]},
        "card": {
            "kind": "list",
            "items": [
                {
                    "title": a["title"],
                    "sub": a["label"],
                    "chip": "Chưa xem" if a["status"] == "open" else "Đã xem",
                    "tone": "bad" if a["status"] == "open" else "",
                }
                for a in found[:6]
            ],
        },
    }


async def contacts(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The RM's latest contacts with their families (KPI-06)."""
    from contacts import store as contact_store
    from people import auth

    mine = auth.visible(fixtures.client_ids())
    rows = contact_store.recent(mine, limit=10)
    if not rows:
        return {"text": "Chưa ghi liên hệ nào với các gia đình của bạn.", "data": {"contacts": 0}}
    text = f"{len(rows)} liên hệ gần nhất. " + " ".join(
        f"{k + 1}) {_name(r['family_id'])}: {r['channel_label']}{' (từ tín hiệu)' if r['from_signal'] else ''}."
        for k, r in enumerate(rows[:4])
    )
    return {"text": text, "data": {"contacts": len(rows)}}


# -- writes (planned, confirmed, read back) ----------------------------------------------------

OPTIONS = {"light": "phương án nhẹ", "heavy": "phương án mạnh"}


async def plan_propose(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from scenarios.graph import scenario_flow

    sid = STRESS.get(args.get("scenario"), "vni_30")
    want = args.get("option") if args.get("option") in OPTIONS else "light"
    r = (await _graph(scenario_flow, client_id=_need_client(ctx), scenario=sid, params=None, scope=ctx.scope))["result"]
    option = next((o for o in r["options"] if o["id"] == want), None)
    if option is None:
        raise ToolFailed(f"Kịch bản {r['title']} không có {OPTIONS[want]}")
    return {
        "summary": f"Gửi “{option['title']}” (kịch bản {r['title']}) cho RM duyệt?",
        "args": {"scenario": sid, "title": r["title"], "option": option, "summary": r["summary"]},
    }


async def propose(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from review.graph import propose_flow

    it = (
        await _graph(
            propose_flow,
            client_id=_need_client(ctx),
            option=args.get("option"),
            scenario=args.get("scenario"),
            title=args.get("title"),
            summary=args.get("summary"),
        )
    )["item"]
    return {"text": f"Đã gửi “{it['title']}” cho RM, đang chờ duyệt.", "data": {"id": it["id"]}}


def verify_propose(ctx: Ctx, out: Dict[str, Any]):
    it = wealth_store.review(out["data"]["id"])
    return True if it and it["status"] == "pending" else f"không thấy đề xuất {out['data']['id']} chờ duyệt"


CHANNELS = {"call": "cuộc gọi", "meeting": "buổi gặp", "message": "tin nhắn"}


def plan_contact(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    fam = _family(ctx)
    channel = args.get("channel") if args.get("channel") in CHANNELS else "call"
    note = str(args.get("note") or "").strip()[:500]
    return {
        "summary": f"Ghi một {CHANNELS[channel]} với gia đình {_name(fam)}" + (f": “{note}”" if note else "") + "?",
        "args": {"family_id": fam, "channel": channel, "note": note},
    }


async def contact(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from contacts.graph import contact_flow

    c = (
        await _graph(
            contact_flow,
            family_id=args.get("family_id"),
            channel=args.get("channel"),
            signal=None,
            note=args.get("note"),
            by=ctx.user,
        )
    )["contact"]
    return {
        "text": f"Đã ghi {CHANNELS.get(c.get('channel'), 'liên hệ')} với gia đình {_name(c['family_id'])}.",
        "data": {"id": c["id"], "family_id": c["family_id"]},
    }


def verify_contact(ctx: Ctx, out: Dict[str, Any]):
    from contacts import store as contact_store

    c = contact_store.get(out["data"]["id"])
    return True if c["family_id"] == out["data"]["family_id"] and c["by"] == ctx.user else "liên hệ ghi sai gia đình"


def plan_recommend(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    cid = _need_client(ctx)
    title = str(args.get("title") or "").strip()[:120]
    acts = [str(a).strip()[:300] for a in (args.get("actions") or []) if str(a).strip()][:10]
    if not title or not acts:
        raise ToolFailed("Khuyến nghị cần tiêu đề và ít nhất một việc cần làm")
    return {
        "summary": f"Gửi khuyến nghị “{title}” ({len(acts)} việc) cho {_name(cid)}?",
        "args": {"title": title, "actions": acts},
    }


async def recommend(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from review.graph import recommend_flow

    it = (
        await _graph(
            recommend_flow,
            client_id=_need_client(ctx),
            title=args.get("title"),
            actions=args.get("actions"),
            note="Qua trợ lý",
            by=ctx.user,
        )
    )["item"]
    return {
        "text": f"Đã gửi khuyến nghị “{it['title']}”: {STATUS.get(it['status'], it['status'])}.",
        "data": {"id": it["id"], "status": it["status"]},
    }


def verify_recorded(ctx: Ctx, out: Dict[str, Any]):
    """The queue item read back, in the status the write reported."""
    it = wealth_store.review(out["data"]["id"])
    return True if it and it["status"] == out["data"]["status"] else f"đề xuất {out['data']['id']} không như đã báo"


def plan_specialist(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    it = _review(args.get("item_id"))
    if it["status"] != "pending_specialist":
        raise ToolFailed(f"{it['id']} không chờ chuyên gia duyệt ({STATUS.get(it['status'], it['status'])})")
    decision = args.get("decision") if args.get("decision") in ("approved", "rejected") else "approved"
    note = str(args.get("note") or "").strip()[:1000]
    if decision == "rejected" and len(note) < 10:
        raise ToolFailed("Từ chối cần lý do từ 10 ký tự")
    verb = "Duyệt" if decision == "approved" else "Từ chối"
    return {
        "summary": f"{verb} khuyến nghị “{it['title']}” của {_name(it['client_id'])}?",
        "args": {"item_id": it["id"], "decision": decision, "note": note},
    }


async def specialist(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from review.graph import specialist_flow

    it = (
        await _graph(
            specialist_flow,
            item_id=args.get("item_id"),
            decision=args.get("decision"),
            note=args.get("note"),
            by=ctx.user,
        )
    )["item"]
    return {
        "text": f"Đã ghi: {STATUS.get(it['status'], it['status'])} “{it['title']}”.",
        "data": {"id": it["id"], "status": it["status"]},
    }


def plan_urgent(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from events import store as events_store
    from events.store import EventError

    try:
        ev = events_store.get(str(args.get("event_id") or ""))
    except EventError as exc:
        raise ToolFailed(str(exc)) from None
    urgent = args.get("urgent") is not False
    reason = str(args.get("reason") or "").strip()[:300]
    if urgent and not reason:
        raise ToolFailed("Cần ghi lý do khi đánh dấu khẩn")
    said = f"Đánh dấu khẩn sự kiện “{ev['title']}”: {reason}?" if urgent else f"Bỏ dấu khẩn của “{ev['title']}”?"
    return {"summary": said, "args": {"event_id": ev["id"], "urgent": urgent, "reason": reason}}


async def urgent(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from events.graph import event_urgent_flow

    ev = (
        await _graph(
            event_urgent_flow,
            event_id=args.get("event_id"),
            urgent=args.get("urgent"),
            reason=args.get("reason"),
            by=ctx.user,
        )
    )["event"]
    flag = bool(ev.get("urgent"))
    return {
        "text": f"Đã {'đánh dấu khẩn' if flag else 'bỏ dấu khẩn'} sự kiện “{ev['title']}”.",
        "data": {"id": ev["id"], "urgent": flag},
    }


def verify_urgent(ctx: Ctx, out: Dict[str, Any]):
    from events import store as events_store

    ev = events_store.get(out["data"]["id"])
    return True if bool(ev.get("urgent")) == out["data"]["urgent"] else "dấu khẩn không như đã báo"


def plan_ack(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from control import alerts

    a = next((x for x in alerts.for_role(ctx.role) if x["id"] == str(args.get("alert_id") or "")), None)
    if a is None:
        raise ToolFailed(f"Không có cảnh báo {args.get('alert_id')} cho vai trò này")
    if a["status"] != "open":
        raise ToolFailed(f"Cảnh báo {a['id']} đã được xem")
    return {
        "summary": f"Đánh dấu đã xem cảnh báo “{a['title']}”?",
        "args": {"alert_id": a["id"], "note": str(args.get("note") or "").strip()[:300]},
    }


async def ack(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from control.graph import alert_ack_flow

    a = (await _graph(alert_ack_flow, alert_id=args.get("alert_id"), by=ctx.user, note=args.get("note")))["alert"]
    return {"text": f"Đã đánh dấu đã xem cảnh báo {a['id']}.", "data": {"id": a["id"]}}


def verify_ack(ctx: Ctx, out: Dict[str, Any]):
    from control import db

    with db.tx() as con:
        row = con.execute("select status from alerts where id = ?", (out["data"]["id"],)).fetchone()
    return True if row and row["status"] == "acked" else f"cảnh báo đang ở {row and row['status']}"


ITEM = Param(str, "mã đề xuất, lấy từ công cụ de_xuat")
CATALOGUE: Dict[str, Tool] = {
    t.name: t
    for t in [
        Tool(
            "dong_luc",
            "chính sách, biến động vĩ mô và dự án đang tác động tới tài sản, quy ra tiền",
            ("client", "rm"),
            drivers,
            page="chinh-sach",
        ),
        Tool(
            "tim_kiem",
            "tìm tài sản, mục tiêu, khách hàng, sự kiện, tin trong những gì vai trò được xem",
            ("client", *STAFF),
            search,
            params={"q": Param(str, "từ khóa cần tìm, ngắn")},
        ),
        Tool(
            "de_xuat",
            "các đề xuất, khuyến nghị trong hàng chờ và trạng thái của chúng",
            ("client", "rm", "specialist"),
            queue,
            page="hang-cho",
        ),
        Tool("su_kien", "các sự kiện của CIO, khẩn hay không, bị giữ hay không", ("cio",), events, page="su-kien"),
        Tool(
            "canh_bao_he_thong",
            "các cảnh báo hệ thống vai trò này cần xem",
            ("cio", "compliance", "admin"),
            system_alerts,
            page="he-thong",
        ),
        Tool("lien_he", "các lần liên hệ gần nhất với các gia đình", ("rm",), contacts, page="hom-nay"),
        Tool(
            "gui_de_xuat",
            "gửi một phương án của kịch bản sốc cho RM duyệt",
            ("client", "rm"),
            propose,
            write=True,
            args={"scenario": list(STRESS), "option": list(OPTIONS)},
            page="ke-hoach",
            plan=plan_propose,
            verify=verify_propose,
        ),
        Tool(
            "ghi_lien_he",
            "ghi lại một lần liên hệ với gia đình khách hàng đang chọn",
            ("rm",),
            contact,
            write=True,
            args={"channel": list(CHANNELS)},
            params={"note": Param(str, "ghi chú ngắn về lần liên hệ", "")},
            page="hom-nay",
            plan=plan_contact,
            verify=verify_contact,
        ),
        Tool(
            "khuyen_nghi",
            "gửi khuyến nghị hành động cho khách hàng đang chọn",
            ("rm",),
            recommend,
            write=True,
            params={
                "title": Param(str, "tiêu đề khuyến nghị"),
                "actions": Param(List[str], "các việc cần làm, mỗi việc một câu"),
            },
            page="duyet",
            plan=plan_recommend,
            verify=verify_recorded,
        ),
        Tool(
            "chuyen_gia_duyet",
            "chuyên gia duyệt hoặc từ chối một khuyến nghị đang chờ mình",
            ("specialist",),
            specialist,
            write=True,
            args={"decision": ["approved", "rejected"]},
            params={"item_id": ITEM, "note": Param(str, "lý do; bắt buộc khi từ chối", "")},
            page="hang-cho",
            plan=plan_specialist,
            verify=verify_recorded,
        ),
        Tool(
            "danh_dau_khan",
            "đánh dấu khẩn một sự kiện (kèm lý do) hoặc bỏ dấu khẩn",
            ("cio",),
            urgent,
            write=True,
            params={
                "event_id": Param(str, "mã sự kiện, lấy từ công cụ su_kien"),
                "urgent": Param(bool, "true để đánh dấu, false để bỏ", True),
                "reason": Param(str, "lý do khi đánh dấu khẩn", ""),
            },
            page="su-kien",
            plan=plan_urgent,
            verify=verify_urgent,
        ),
        Tool(
            "da_xem_canh_bao",
            "đánh dấu đã xem một cảnh báo hệ thống",
            ("cio", "compliance", "admin"),
            ack,
            write=True,
            params={
                "alert_id": Param(str, "mã cảnh báo, lấy từ công cụ canh_bao_he_thong"),
                "note": Param(str, "ghi chú", ""),
            },
            page="he-thong",
            plan=plan_ack,
            verify=verify_ack,
        ),
    ]
}

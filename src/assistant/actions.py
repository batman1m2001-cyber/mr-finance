"""The app's served graphs as assistant tools (A1, ADR-0032): reads beyond the Copilot's, and the writes a person
may ask for in a sentence. Each runs the graph the page posts to, as the person, so the server's role, family
and separation-of-duty checks apply unchanged; a write is planned (the line the person confirms, its arguments
resolved here), then read back by its verifier.

Left to their pages, deliberately: the four-eyes governance decisions (configuration versions, approving CIO
views, reviewing runs, newsletters, policy documents, research release, the market model), grouping news into
events, releasing held news and the client's risk test. Each needs the person to read evidence on that page; the
assistant opens the page (``mo_trang``) instead of acting. The client's own files are the exception (ADR-0041):
``them_tu_tep``'s confirm line lists every item and the total, which is that evidence. Starting Agent CIO, re-running the
challenger and running a background job are not decisions (owner 2026-10-18): they are writes here, on a Xác nhận."""

from __future__ import annotations

from typing import Any, Dict, List

from assistant.base import Ctx, Param, Tool, ToolFailed
from assistant.tools import STRESS, _family, _graph, _need_client, _vnd
from control.jobs import RUNNABLE
from wealth import fixtures
from wealth import store as wealth_store

STAFF = ("rm", "cio", "admin")
STATUS = {
    "pending": "chờ RM duyệt",
    "pending_specialist": "chờ chuyên gia duyệt",  # kept for items queued before OWN-FB-18
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


KIND = {"policy": "chính sách", "macro": "vĩ mô", "infrastructure": "dự án hạ tầng"}


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
        # every factor, as the page lists them: “what do the property rules cost me?” needs them all (stress D27)
        + " Từng yếu tố: "
        + "; ".join(
            f"{a['title']} ({KIND.get(a['kind'], 'yếu tố khác')}, {a['status_label'].lower()}) "
            f"{_vnd(a['impact'], True)}"
            for a in found
        )
        + "."
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
    found = (await _graph(search_flow, q=q, role=ctx.role, client_id=ctx.client_id, scope=ctx.scope))["search"]
    hits = found["hits"]
    if not hits:
        return {"text": f"Không tìm thấy gì cho “{q}” trong những gì bạn được xem.", "data": {"hits": 0, "total": 0}}
    total = found.get("total", len(hits))  # every match, counted; ``hits`` is at most six of each kind
    shown = f"{len(hits)} / {total}" if total > len(hits) else str(total)
    return {
        "text": f"{shown} kết quả cho “{q}”: " + "; ".join(h["label"] for h in hits[:5]) + ".",
        "data": {
            "hits": len(hits),
            "total": total,
            "items": [{"label": h["label"], "route": h["route"]} for h in hits[:10]],
        },
        "card": {
            "kind": "list",
            "items": [{"title": h["label"], "sub": h.get("sub") or "", "route": h["route"]} for h in hits[:8]],
        },
    }


async def queue(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    """The proposals and recommendations in the queue: the selected client's (client, RM), or the RM's whole book."""
    from people import store as people

    def family(r: Dict[str, Any]) -> str:
        return people.client(r["client_id"]).get("member_of") or r["client_id"]

    if ctx.role == "rm" and not ctx.client_id:  # no family picked: the RM's whole book (staff stress test D02)
        from desk import reads as desk_reads

        book = set(desk_reads.book_of({"id": ctx.user, "role": "rm"}))
        items = [r for r in wealth_store.reviews() if family(r) in book]
    else:
        items = wealth_store.reviews(client_id=_need_client(ctx))
    if not items:
        return {"text": "Không có đề xuất nào trong hàng chờ.", "data": {"items": []}}
    waiting = [r for r in items if r["status"] in ("pending", "pending_specialist")]
    text = f"{len(items)} đề xuất, {len(waiting)} đang chờ. " + " ".join(
        f"{k + 1}) {r['title']} ({_name(r['client_id'])}, mã {r['id']}) — {STATUS.get(r['status'], r['status'])}."
        for k, r in enumerate(items[:4])
    )
    return {
        "text": text,
        "data": {
            "items": [{"id": r["id"], "title": r["title"], "status": r["status"]} for r in items[:20]],
            "total": len(items),  # ``reviews`` reads every row (no cap), so its length is the total
            "waiting": len(waiting),
        },
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
    """The CIO's events, newest first: urgent or not, held for the restricted list or not."""
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
        return {"text": "Không có cảnh báo hệ thống nào.", "data": {"alerts": [], "total": 0, "open": 0}}
    n = alerts.counts(ctx.role)  # counted in the database: ``for_role`` is a page of 50
    text = f"{n['total']} cảnh báo hệ thống, {n['open']} chưa ai xem. " + " ".join(
        f"{k + 1}) {a['label']}: {a['title']}." for k, a in enumerate(found[:3])
    )
    return {
        "text": text,
        "data": {
            "alerts": [{"id": a["id"], "title": a["title"], "status": a["status"]} for a in found[:20]],
            "total": n["total"],
            "open": n["open"],
        },
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
    # why it went straight through: without it the assistant told the RM an approved recommendation “may have
    # skipped the specialist” (staff stress test, rm-act-03); there is no specialist step since OWN-FB-18
    why = " RM duyệt là đủ: khuyến nghị đã tới khách." if it["status"] == "approved" else ""
    return {
        "text": f"Đã gửi khuyến nghị “{it['title']}”: {STATUS.get(it['status'], it['status'])}.{why}",
        "data": {"id": it["id"], "status": it["status"]},
    }


def verify_recorded(ctx: Ctx, out: Dict[str, Any]):
    """The queue item read back, in the status the write reported."""
    it = wealth_store.review(out["data"]["id"])
    return True if it and it["status"] == out["data"]["status"] else f"đề xuất {out['data']['id']} không như đã báo"


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


# -- the agents and the jobs (owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md A): started on a Xác nhận; what they
# lead to (a view's approval, a run's review) stays on its page with its second person

MODES = {"live": "trực tiếp (mô hình thật)", "mock": "mô phỏng (quy tắc, không gọi mô hình)"}


def plan_agent(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from events import store as events_store
    from events.store import EventError
    from views import agents
    from views import queue as agent_queue
    from views import store as views_store

    try:
        ev = events_store.get(str(args.get("event_id") or ""))
    except EventError as exc:
        raise ToolFailed(str(exc)) from None
    if ev["blocked"]:
        held = ", ".join(ev["held"])
        raise ToolFailed(f"Sự kiện “{ev['title']}” đang bị giữ chờ CIO cho đi tiếp ({held}): chưa chạy được")
    asked = str(args.get("mode") or "") or None
    try:
        mode = agents.resolve_mode(asked)
    except agents.AgentError as exc:
        raise ToolFailed(str(exc)) from None
    open_ = [j for j in agent_queue.for_event(ev["id"]) if j["status"] in ("queued", "running")]
    if open_:
        raise ToolFailed(f"Agent CIO đã có lần chờ chạy cho sự kiện này ({open_[0]['id']}, {open_[0]['status']})")
    had = len(views_store.for_event(ev["id"]))
    again = f" (sự kiện đã có {had} nhận định; lần này thêm một bản nháp mới)" if had else ""
    return {
        "summary": f"Chạy Agent CIO cho sự kiện “{ev['title']}”, chế độ {MODES[mode]}{again}?",
        "args": {"event_id": ev["id"], "mode": asked},
    }


async def agent_run(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from views.graph import agent_queue_flow

    job = (await _graph(agent_queue_flow, event_id=args.get("event_id"), by=ctx.user, mode=args.get("mode")))["job"]
    return {
        "text": f"Đã xếp Agent CIO chạy cho sự kiện {job['event_id']} (lần {job['id']}, chế độ {MODES[job['mode']]}). "
        "Nhận định ra là bản nháp: qua Agent Phản biện, rồi bạn duyệt ở trang Sự kiện & nhận định; tiến độ ở trang "
        "Việc nền.",
        "data": {"id": job["id"], "event_id": job["event_id"]},
    }


def verify_agent(ctx: Ctx, out: Dict[str, Any]):
    from views import queue as agent_queue

    j = agent_queue.get(out["data"]["id"])
    return True if j["event_id"] == out["data"]["event_id"] else "lần chạy không khớp sự kiện"


def plan_challenge(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from events import store as events_store
    from views import decide as view_decide
    from views import store as views_store

    try:
        v = views_store.get(str(args.get("view_id") or ""))
    except KeyError:
        raise ToolFailed(f"Không có nhận định {args.get('view_id')}") from None
    if v["status"] not in view_decide.FROM["challenge"]:
        raise ToolFailed(
            f"Nhận định {v['id']} đang ở {STATUS_VIEW.get(v['status'], v['status'])}: Agent Phản biện chỉ chạy lại khi "
            "lần trước lỗi; sửa nhận định cũng chạy lại nó"
        )
    title = events_store.get(v["event_id"])["title"]
    why = f"; lần trước lỗi: {v['challenge_error']}" if v.get("challenge_error") else ""
    return {
        "summary": f"Chạy lại Agent Phản biện cho nhận định {v['id']} (sự kiện “{title}”{why})?",
        "args": {"view_id": v["id"], "before": len(views_store.challenges(v["id"]))},
    }


async def challenge(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from views import store as views_store
    from views.graph import decide_flow

    await _graph(decide_flow, view_id=args.get("view_id"), action="challenge", by=ctx.user)
    v = views_store.get(str(args.get("view_id")))
    found = views_store.latest_challenge(v["id"])
    ran = len(views_store.challenges(v["id"])) > int(args.get("before") or 0)
    text = (
        f"Đã chạy lại Agent Phản biện: {len(found['findings'])} phát hiện; nhận định {v['id']} chờ bạn duyệt ở trang "
        "Sự kiện & nhận định."
        if ran
        else f"Chưa phản biện được, Agent Phản biện lại lỗi: {v.get('challenge_error') or 'không rõ lý do'}. Nhận định "
        "vẫn chờ phản biện."
    )
    return {"text": text, "data": {"id": v["id"], "ran": ran, "status": v["status"]}}


def verify_challenge(ctx: Ctx, out: Dict[str, Any]):
    from views import store as views_store

    v = views_store.get(out["data"]["id"])
    if out["data"]["ran"]:
        return True if v["status"] == "PENDING_APPROVAL" else f"nhận định đang ở {v['status']}"
    return True if v.get("challenge_error") else "không thấy lỗi đã báo"


def plan_job(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from control import jobs

    job = str(args.get("job") or "")
    if job not in jobs.RUNNABLE:
        raise ToolFailed(f"Việc {job!r} không chạy tay được")
    busy = jobs.running(job)
    if busy:
        raise ToolFailed(f"{jobs.label(job)} đang chạy (lần {busy['id']}); chờ nó xong")
    return {"summary": f"Chạy ngay việc nền “{jobs.label(job)}”?", "args": {"job": job}}


async def job_run(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from control.graph import job_run_flow

    r = (await _graph(job_run_flow, job=args.get("job"), by=ctx.user))["run"]
    return {
        "text": f"Đã bắt đầu “{r['label']}” (lần {r['id']}). Việc chạy nền; kết quả ở trang Việc nền.",
        "data": {"id": r["id"], "job": r["job"]},
    }


def verify_job(ctx: Ctx, out: Dict[str, Any]):
    from control import jobs

    r = jobs.get(out["data"]["id"])
    return True if r["job"] == out["data"]["job"] and r["by"] == ctx.user else "lần chạy không khớp"


STATUS_VIEW = {
    "DRAFTING": "đang soạn",
    "PENDING_APPROVAL": "chờ CIO duyệt",
    "APPROVED": "đã duyệt",
    "AGENT_ERROR": "agent lỗi",
    "REWORK_REQUESTED": "bị trả lại",
    "REJECTED": "bị bác",
    "WITHDRAWN": "đã thu hồi",
    "SUPERSEDED": "đã thay thế",
}


# -- Admin's users and roles (Q-25): read, and a request filed on a Xác nhận; a second Admin decides on the page


async def accounts_read(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from people import accounts

    d = accounts.read()
    by_role: Dict[str, List[str]] = {}
    for p in d["people"]:
        by_role.setdefault(d["roles"].get(p["role"], p["role"]), []).append(
            p["name"] + (" (đã khoá)" if p["disabled"] else "") + (" (demo)" if p["protected"] else "")
        )
    waiting = [r for r in d["requests"] if r["status"] == "pending"]

    def said(r):
        what = f"{r['name']}" + (f", {r.get('role_label')}" if r["kind"] in ("add", "role") else "")
        return f"{r['id']} {r['label']}: {what}, {r['by']} đề xuất"

    text = (
        f"{len(d['people'])} tài khoản nhân viên — "
        + "; ".join(f"{k}: {', '.join(v)}" for k, v in by_role.items())
        + ". "
        + (
            f"Yêu cầu chờ Quản trị thứ hai duyệt: {'; '.join(said(r) for r in waiting)}. "
            if waiting
            else "Không yêu cầu nào chờ. "
        )
        + ("Tài khoản demo được giữ nguyên khi bật tài khoản demo. " if d["demo_protected"] else "")
        + "Duyệt hay từ chối ở trang Tài khoản và vai trò, bởi một Quản trị khác người đề xuất."
    )
    return {
        "text": text,
        "data": {"people": len(d["people"]), "waiting": [r["id"] for r in waiting]},
        "focus": ["people"],
        "sources": ["Tài khoản và vai trò"],
    }


def _staff_named(who: str) -> Dict[str, Any]:
    from copilot.scrub import fold
    from people import accounts

    key = fold(str(who or "")).strip()
    people = [p for p in accounts.read()["people"]]
    hit = [p for p in people if key in (p["id"].lower(), p["login"].lower())] or [
        p for p in people if key and key in fold(p["name"])
    ]
    if len(hit) != 1:
        names = ", ".join(f"{p['name']} ({p['id']})" for p in hit[:5])
        raise ToolFailed(f"Không xác định được một tài khoản cho “{who}”" + (f": {names}" if names else ""))
    return hit[0]


def plan_account(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from control import roles
    from people import accounts, store

    kind = str(args.get("kind") or "")
    if kind not in accounts.KINDS:
        raise ToolFailed(f"Loại yêu cầu là một trong {', '.join(accounts.KINDS)}")
    out = {"kind": kind, "note": str(args.get("note") or "").strip()[:300]}
    role = str(args.get("role") or "")
    if kind == "add":
        out.update(name=args.get("name") or "", email=args.get("email") or "", role=role, title=args.get("title") or "")
        with store._db() as con:
            try:
                clean = accounts._check(con, "add", out, ctx.user)
            except accounts.AccountError as exc:
                raise ToolFailed(str(exc)) from None
        said = (
            f"Gửi yêu cầu thêm tài khoản {clean['name']} ({clean['email']}), vai trò {roles.ROLE_LABELS[clean['role']]}"
        )
    else:
        p = _staff_named(args.get("person") or "")
        out.update(person_id=p["id"], role=role)
        with store._db() as con:
            try:
                accounts._check(con, kind, out, ctx.user)
            except accounts.AccountError as exc:
                raise ToolFailed(str(exc)) from None
        what = {"role": f"đổi vai trò của {p['name']} sang {roles.ROLE_LABELS.get(role, role)}",
                "disable": f"khoá tài khoản {p['name']}", "enable": f"mở lại tài khoản {p['name']}",
                "reset": f"đặt lại mật khẩu của {p['name']}"}[kind]  # fmt: skip
        said = f"Gửi yêu cầu {what}"
    return {"summary": f"{said} (một Quản trị khác duyệt ở trang Tài khoản và vai trò)?", "args": out}


async def account_request(ctx: Ctx, args: Dict[str, Any]) -> Dict[str, Any]:
    from people.graph import account_request_flow

    keys = ("kind", "person_id", "email", "role", "title", "note")
    body = {k: args.get(k) or "" for k in keys}
    r = (await _graph(account_request_flow, by=ctx.user, full_name=args.get("name") or "", **body))["request"]
    return {
        "text": f"Đã gửi yêu cầu {r['id']} ({r['label']}): chờ một Quản trị khác duyệt ở trang Tài khoản và vai trò."
        + (
            f" Khi duyệt, Quản trị duyệt nhận mã dùng một lần để trao tận tay {r.get('name') or 'nhân viên đó'}."
            if r["kind"] in ("add", "reset")
            else ""
        ),
        "data": {"id": r["id"], "kind": r["kind"]},
    }


def verify_account(ctx: Ctx, out: Dict[str, Any]):
    from people import accounts

    r = accounts.get(out["data"]["id"])
    return True if r["status"] == "pending" and r["by"] == ctx.user else f"yêu cầu đang ở {r['status']}"


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
            ("client", "rm"),
            queue,
            page="hang-cho",
        ),
        Tool("su_kien", "các sự kiện của CIO, khẩn hay không, bị giữ hay không", ("cio",), events, page="su-kien"),
        Tool(
            "canh_bao_he_thong",
            "các cảnh báo hệ thống vai trò này cần xem",
            ("cio", "admin"),
            system_alerts,
            page="he-thong",
        ),
        Tool("lien_he", "các lần liên hệ gần nhất với các gia đình", ("rm",), contacts, page="hom-nay"),
        Tool(
            "gui_de_xuat",
            "gửi một phương án của kịch bản sốc cho RM duyệt (option light là “phương án nhẹ”, heavy là “phương án "
            "mạnh”: nói với người dùng bằng tên tiếng Việt)",
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
            "chay_agent_cio",
            "xếp Agent CIO chạy cho một sự kiện (ra bản nháp nhận định, qua Agent Phản biện, CIO duyệt ở trang): mode "
            "live là mô hình thật, mock là mô phỏng; bỏ trống mode để theo cấu hình",
            ("cio",),
            agent_run,
            write=True,
            args={"mode": ["", "live", "mock"]},
            params={"event_id": Param(str, "mã sự kiện, lấy từ công cụ agent_nen hoặc su_kien")},
            page="viec-nen",
            plan=plan_agent,
            verify=verify_agent,
        ),
        Tool(
            "phan_bien_lai",
            "chạy lại Agent Phản biện cho một nhận định mà lần phản biện trước lỗi",
            ("cio",),
            challenge,
            write=True,
            params={"view_id": Param(str, "mã nhận định, lấy từ công cụ agent_nen")},
            page="viec-nen",
            plan=plan_challenge,
            verify=verify_challenge,
            timeout=120.0,
        ),
        Tool(
            "chay_viec_nen",
            "Quản trị chạy ngay một việc nền (lấy tin, dữ liệu thị trường, quét chính sách, kiểm tra chuỗi nhật ký, "
            "đồng bộ vùng AI, chấm độ chính xác) khi được bảo “chạy ngay”, “chạy việc …”: lần chạy được ghi lại",
            ("admin",),
            job_run,
            write=True,
            args={"job": list(RUNNABLE)},
            page="viec-nen",
            plan=plan_job,
            verify=verify_job,
        ),
        Tool(
            "tai_khoan",
            "Quản trị xem các tài khoản nhân viên theo vai trò, tài khoản đã khoá và các yêu cầu tài khoản đang chờ "
            "Quản trị thứ hai duyệt",
            ("admin",),
            accounts_read,
            page="tai-khoan",
        ),
        Tool(
            "yeu_cau_tai_khoan",
            "Quản trị gửi yêu cầu về tài khoản nhân viên (kind add: thêm tài khoản, role: đổi vai trò, disable: khoá, "
            "enable: mở lại, reset: đặt lại mật khẩu); một Quản trị khác duyệt ở trang, trợ lý không duyệt",
            ("admin",),
            account_request,
            write=True,
            args={
                "kind": ["add", "role", "disable", "enable", "reset"],
                "role": ["", "rm", "cio", "admin"],
            },  # fmt: skip
            params={
                "person": Param(str, "tên, email hay mã của nhân viên (không dùng khi thêm tài khoản)", ""),
                "name": Param(str, "họ tên, khi thêm tài khoản", ""),
                "email": Param(str, "email làm tên đăng nhập, khi thêm tài khoản", ""),
                "title": Param(str, "chức danh, khi thêm tài khoản", ""),
                "note": Param(str, "ghi chú cho người duyệt", ""),
            },
            page="tai-khoan",
            plan=plan_account,
            verify=verify_account,
        ),
        Tool(
            "da_xem_canh_bao",
            "đánh dấu đã xem một cảnh báo hệ thống",
            ("cio", "admin"),
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

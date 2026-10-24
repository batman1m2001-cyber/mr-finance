"""What each staff role's desk shows (FEAT-41, ADR-0036): counts and short lists composed from the stores the
existing reads use — the same rules, the same filters — so a desk never says a number its pages would not. The
role's assistant reads the same composition (assistant/desktools.py), so the screen and the assistant agree.

Read-only. ``desk(role, viewer)`` is the one entry point; the role comes from the session (app/web.py)."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from apply import reads as apply_reads
from apply import run as apply_run
from control import roles

ROUTE = {
    "cio": "#/cio",
    "rm": "#/rm",
    "admin": "#/admin",
}  # each role's desk address; a page's address is its menu id under it


def _event_title(event_id: str) -> str:
    from events import store as events

    try:
        return events.get(event_id)["title"]
    except Exception:  # an event the store no longer has: its id says enough
        return event_id


REL_RANK = {"high": 3, "medium": 2, "low": 1}


def _signal(ev: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """What a decision row says of its news (OWN-FB-09, 10): the impact level (the highest relevance of its news),
    the news group (the event's type), its outlets and whether they are domestic, international or both."""
    if not ev:
        return {"level": None, "group": None, "sources": [], "scope": None}
    items = ev.get("news") or []
    level = max(
        (i.get("relevance") for i in items if i.get("relevance")), key=lambda r: REL_RANK.get(r, 0), default=None
    )
    kinds = {i.get("kind") for i in items if i.get("kind")} or set(ev.get("kinds") or [])
    return {
        "level": level,
        "group": ev.get("type"),
        "sources": sorted({i["source"] for i in items if i.get("source")}),
        "outlets": sorted({i["outlet"] for i in items if i.get("outlet")}),
        "scope": "both" if len(kinds) > 1 else next(iter(kinds), None),
    }


def _scenario(r: Dict[str, Any], names: Dict[str, str]) -> Dict[str, Any]:
    """An effective run as the CIO's desk names it (OWN-FB-12): a scenario, by its news and its date, never its id."""
    from events import store as events

    total = r["exposure"]["total"]
    top = sorted((f for f in total if total[f]), key=lambda f: -abs(total[f]))[:6]
    try:
        ev = events.get(r["event_id"])
    except Exception:  # an event the store no longer has
        ev = None
    return {
        "run_id": r["id"],
        "event": ev["title"] if ev else r["event_id"],
        "group": ev.get("type") if ev else None,
        "date": r.get("price_date"),
        "created": r["created"],
        "expected_3m": r["totals"]["expected_3m"],
        "families": r["families"],
        "pre_review": r["totals"]["pre_review"],
        "factors": [{"id": f, "name": names.get(f, f), "value": total[f]} for f in top],
        "ranking": [
            {
                k: x[k]
                for k in ("family_id", "name", "expected_3m", "expected_3m_pct", "p10_3m", "p10_3m_pct", "pre_review")
                if k in x
            }  # fmt: skip
            for x in r.get("ranking") or []
        ],
        "route": f"#/cio/phoi-nhiem/{r['id']}",
    }


def cio(viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Decision board (SCR-CIO-15, OWN-FB-07…13): the news-to-family pipeline, what waits for the CIO's decision
    (each row with its level, news group, outlets and scope), and the scenarios in force with the families ranked.
    The inbox is drawn on the board by its own read (GET /api/news/inbox)."""
    from control import config
    from engine import default_model
    from events import store as events
    from news import store as news
    from newsletter import store as letters
    from policy import store as policy
    from research import store as research
    from views import ops as view_ops

    me = (viewer or {}).get("id") or "cio"
    names = {f.id: f.name for f in default_model().factors}

    fresh_n = news.count(status="new")  # counted in the database: a page of rows is never the total
    high_n = news.count(status="new", relevance="high")
    high = news.inbox(status="new", relevance="high", limit=5)

    evs = events.listing()
    states = []
    for ev in evs:
        vs = view_ops.event_views(ev["id"])
        latest = max(vs, key=lambda v: v["version"]) if vs else None
        states.append({"event": ev, "views": vs, "latest": latest})
    by_id = {s["event"]["id"]: s["event"] for s in states}
    waiting_views = [s for s in states if s["latest"] and s["latest"]["status"] == "PENDING_APPROVAL"]
    no_view = [s for s in states if not s["views"] and not s["event"].get("blocked")]
    held = [s for s in states if s["event"].get("blocked")]

    runs = apply_run.runs()
    effective = [r for r in runs if r["status"] == "EFFECTIVE"]
    review = [r for r in runs if r["status"] == "NEEDS_CIO_REVIEW"]
    computing = [r for r in runs if r["status"] in ("COMPUTING", "POST_CHECKING")]
    flagged = sorted({x["family_id"] for r in effective for x in r.get("ranking") or [] if x.get("pre_review")})
    families = sorted({x["family_id"] for r in effective for x in r.get("ranking") or []})
    cases = apply_reads.rm_today(None)["cases"]
    rm_families = sorted({c["family_id"] for c in cases})  # as Hôm nay groups them
    name_of = {x["family_id"]: x["name"] for r in effective for x in r.get("ranking") or []}
    name_of.update({c["family_id"]: c["name"] for c in cases})

    decide: List[Dict[str, Any]] = []
    for s in waiting_views:
        v = s["latest"]
        decide.append({"kind": "view", "id": v["id"], "title": s["event"]["title"], "status": "Chờ CIO duyệt",
                       "at": v["created"], "route": f"#/cio/nhan-dinh/{v['id']}", **_signal(s["event"])})  # fmt: skip
    for r in review:
        decide.append({"kind": "run", "id": r["id"], "title": _event_title(r["event_id"]), "status": r["status_label"],
                       "at": r["created"], "route": f"#/cio/ap-dung/{r['id']}",
                       **_signal(by_id.get(r["event_id"]))})  # fmt: skip
    for k in config.overview():
        p = k["pending"]
        if p and k["owner"] == "cio":
            mine = p.get("proposed_by") == me and k["two_person"]
            decide.append({"kind": "config", "id": p["id"], "title": k["label"],
                           "status": "Chờ một CIO khác duyệt" if mine else "Chờ CIO duyệt",
                           "at": p["created"], "route": "#/cio/cau-hinh", **_signal(None)})  # fmt: skip
    # OWN-FB-18: what waited for Compliance waits for the CIO now; a CIO never approves their own (four eyes)
    for n in letters.listing():
        if n["status"] == "RETURNED" and n.get("author") == me:
            status = "Bị trả lại"
        elif n["status"] == "PENDING_COMPLIANCE":
            status = "Chờ CIO khác duyệt" if n.get("author") == me else "Chờ bạn duyệt"
        else:
            continue
        decide.append({"kind": "letter", "id": n["id"], "title": n.get("title") or n["id"], "status": status,
                       "at": n["created"], "route": f"#/cio/ban-tin/{n['id']}", **_signal(None)})  # fmt: skip
    for i in news.inbox(status="all", held=True, limit=None):
        decide.append({"kind": "held", "id": i["id"], "title": i["title"], "status": "Tin bị giữ",
                       "at": i.get("published") or i.get("ingested"), "route": "#/cio/giu", **_signal(None),
                       "outlets": [i["outlet"]] if i.get("outlet") else []})  # fmt: skip
    for r in research.listing():
        if r["status"] == "PENDING_RELEASE":
            mine = r.get("uploaded_by") == me
            decide.append({"kind": "research", "id": r["id"], "title": r["title"],
                           "status": "Chờ CIO khác phát hành" if mine else "Chờ phát hành", "at": r["created"],
                           "route": "#/cio/nghien-cuu", **_signal(None)})  # fmt: skip
    for x in policy.radar()["documents"]:
        if not x.get("verified") and x["status"] != "dropped":
            mine = x.get("added_by") == me
            decide.append({"kind": "policy", "id": x["id"], "title": x["title"],
                           "status": "Chờ CIO khác xác nhận nguồn" if mine else "Chờ xác nhận nguồn",
                           "at": x["created"], "route": f"#/cio/chinh-sach/{x['id']}", **_signal(None)})  # fmt: skip
    for s in no_view:
        ev = s["event"]
        decide.append({"kind": "event", "id": ev["id"], "title": ev["title"], "status": "Chưa có nhận định",
                       "at": ev["created"], "route": f"#/cio/nhan-dinh/{ev['id']}", **_signal(ev)})  # fmt: skip
    decide.sort(key=lambda x: -(x["at"] or 0))

    scenarios = [_scenario(r, names) for r in effective]  # newest first, as Tác động danh mục opens them
    exposure = None
    if scenarios:
        x = scenarios[0]
        exposure = {**{k: x[k] for k in ("run_id", "event", "expected_3m", "families", "pre_review", "factors",
                                          "route")},
                    "worst": x["ranking"][:3]}  # fmt: skip

    stage = lambda *a: dict(zip(("id", "label", "count", "unit", "waits", "note", "route"), a))  # noqa: E731
    # OWN-FB-08: no Sự kiện stage; the events are counted in Tin's note, their views in Nhận định
    pipeline = [
        stage("news", "Tin", fresh_n, "tin mới", high_n,
              f"{high_n} liên quan cao · {len(evs)} sự kiện" + (f" · {len(held)} bị giữ" if held else ""),
              "#/cio"),
        stage("views", "Nhận định", sum(len(s["views"]) for s in states), "phiên bản",
              len(waiting_views) + len(no_view),
              f"{len(waiting_views)} chờ CIO duyệt · {len(no_view)} sự kiện chưa có nhận định", "#/cio/nhan-dinh"),
        stage("runs", "Lần áp dụng", len(effective), "đang hiệu lực", len(review) + len(computing),
              f"{len(review)} chờ CIO xem lại" + (f" · {len(computing)} đang tính" if computing else ""),
              "#/cio/ap-dung"),
        stage("families", "Gia đình", len(families), "gia đình được tính", len(flagged),
              f"{len(flagged)} chạm ngưỡng RM xem trước", "#/cio/phoi-nhiem"),  # the frame "đến khách hàng"
        stage("rm", "RM", len(rm_families), "gia đình RM cần xem trước", 0, "trên trang Hôm nay của RM",
              "#/cio/do-thi"),
    ]  # fmt: skip
    return {
        "role": "cio",
        "as_of": time.time(),
        "pipeline": pipeline,
        "decide": decide,
        "exposure": exposure,
        "scenarios": scenarios,
        "held": len(held),
        # what Thông tin lists for a stage picked on the pipeline (short; the page has the rest)
        "items": {
            "news": [{"id": i["id"], "title": i["title"], "sub": f"{i['outlet']} · {i.get('label') or ''}".strip(" ·"),
                      "route": "#/cio"} for i in high[:5]],
            "views": [{"id": s["event"]["id"], "title": s["event"]["title"],
                       "sub": "chờ CIO duyệt" if s in waiting_views else "chưa có nhận định",
                       "route": f"#/cio/nhan-dinh/{(s['latest'] or s['event'])['id']}"}
                      for s in waiting_views + no_view][:8],
            "runs": [{"id": r["id"], "title": _event_title(r["event_id"]), "value": r["totals"]["expected_3m"],
                      "sub": f"{r['families']} gia đình · {r['totals']['pre_review']} chạm ngưỡng",
                      "route": f"#/cio/ap-dung/{r['id']}"} for r in effective[:5]],
            "families": [{"id": f, "title": name_of.get(f, f), "sub": "chạm ngưỡng RM xem trước"} for f in flagged],
            "rm": [{"id": f, "title": name_of.get(f, f), "sub": "trên trang Hôm nay của RM"} for f in rm_families],
        },
    }  # fmt: skip


URGENCY = {3: "Cần gọi ngay", 2: "Cần xử lý", 1: "Nhắc", 0: "Ổn"}
TASK_URGENCY = {"contact_now": 3, "confirm_goal": 2, "remind": 1}


def book_of(viewer: Optional[Dict[str, Any]]) -> List[str]:
    """The RM's families, as Hôm nay reads them: the viewer's assigned families (sign-in on), the account's when
    the assistant asks for it, every family with sign-in off; never one the request may not see."""
    from people import auth
    from people import store as people
    from wealth import fixtures

    v = viewer or {}
    if v.get("families") is not None:
        fams = list(v["families"])
    elif v.get("id") and v.get("role") == "rm":
        fams = people.families_of(v["id"])
    else:
        fams = fixtures.client_ids()
    return auth.visible(sorted(fams))


def rm(viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Sổ khách hàng (SCR-RM-07): the RM's families around the RM, nearer when they need the RM sooner — a family at
    the pre-review threshold of an effective run or a goal task to contact now, a proposal waiting for the RM or a
    goal to confirm, a reminder — with what Hôm nay, the approval queue and the contact log say of each."""
    from people import store as people
    from wealth import fixtures
    from wealth import store as reviews

    book = book_of(viewer)
    today = apply_reads.rm_today(book)
    mine = set(book)
    # every member's family, to keep the queue to the book: from the people table, unchecked — the checked read
    # refuses a family the RM may not see inside a served turn, and this map is never shown (only the book's are)
    heads = {c: people.client(c).get("member_of") or c for c in people.client_ids(True)}
    waiting = [
        r
        for r in reviews.reviews(status="pending")
        if r["kind"] != "rm_note" and heads.get(r["client_id"], r["client_id"]) in mine
    ]  # what the RM decides on Duyệt đề xuất (pending, not the RM's own notes)

    # one row per family on the call list, worst first (as Hôm nay groups it)
    calls: Dict[str, Dict[str, Any]] = {}
    for c in today["cases"]:
        f = calls.setdefault(c["family_id"], {"family_id": c["family_id"], "name": c["name"], "worst": c,
                                              "expected_3m": 0, "events": []})  # fmt: skip
        f["expected_3m"] += c["expected_3m"]
        f["events"].append(c["event"]["title"])
        if c["p10_3m_pct"] < f["worst"]["p10_3m_pct"]:
            f["worst"] = c
    call_list = sorted(calls.values(), key=lambda f: f["worst"]["p10_3m_pct"])

    effective = apply_run.runs(statuses=("EFFECTIVE",))  # what an RM reads: post-checked runs only
    families = []
    for fid in book:
        rec = fixtures.summary(fid)
        rows = [(r, x) for r in effective for x in r.get("ranking") or [] if x["family_id"] == fid]
        tasks = [t for t in today["goal_tasks"] if t["family_id"] == fid]
        props = [r for r in waiting if heads.get(r["client_id"], r["client_id"]) == fid]
        contact = next((c for c in today["contacts"] if c["family_id"] == fid), None)
        why = []
        if fid in calls:
            w = calls[fid]["worst"]
            p10 = f"{abs(w['p10_3m_pct']) * 100:.1f}".replace(".", ",")
            why.append({"level": 3, "text": f"P10 3 tháng −{p10}% tài sản ròng"})
        why += [{"level": TASK_URGENCY[t["level"]], "text": f"{t['level_label']}: {t['goal']}"} for t in tasks]
        if props:
            why.append({"level": 2, "text": f"{len(props)} đề xuất chờ bạn duyệt"})
        level = max((w["level"] for w in why), default=0)
        families.append({
            "id": fid, "name": rec["name"], "segment": rec.get("segment"), "age": rec.get("age"),
            "occupation": rec.get("occupation"), "city": rec.get("city"),
            "net_worth": rows[0][1]["net_worth"] if rows else None, "net_worth_run": rows[0][0]["id"] if rows else None,
            "level": level, "level_label": URGENCY[level], "why": sorted(why, key=lambda w: -w["level"]),
            "impacts": [{"run_id": r["id"], "event": _event_title(r["event_id"]), "expected_3m": x["expected_3m"],
                         "expected_3m_pct": x["expected_3m_pct"], "pre_review": x["pre_review"]} for r, x in rows[:4]],
            "tasks": len(tasks), "proposals": len(props),
            "last_contact": {k: contact[k] for k in ("at", "channel_label", "from_signal")} if contact else None,
            "control": fid in today["control"],
        })  # fmt: skip
    families.sort(key=lambda f: (-f["level"], f["name"]))
    return {
        "role": "rm",
        "as_of": time.time(),
        "families": families,
        "calls": [
            {
                "family_id": f["family_id"],
                "name": f["name"],
                "p10_3m_pct": f["worst"]["p10_3m_pct"],
                "expected_3m": f["expected_3m"],
                "events": f["events"],
                "run_id": f["worst"]["run_id"],
            }
            for f in call_list
        ],  # fmt: skip
        "threshold_pct": today["threshold_pct"],
        "tasks": [
            {
                k: t.get(k)
                for k in (
                    "family_id",
                    "family_name",
                    "level",
                    "level_label",
                    "goal",
                    "note_title",
                    "milestone",
                    "rm_hint",
                )
            }
            for t in today["goal_tasks"]
        ],  # fmt: skip
        "proposals": [
            {
                "id": r["id"],
                "family_id": heads.get(r["client_id"], r["client_id"]),
                "name": fixtures.client(r["client_id"])["name"],
                "title": r["title"],
                "kind": r["kind"],
                "created": r["created"],
            }
            for r in waiting
        ],  # fmt: skip
        "contacts": [
            {k: c[k] for k in ("id", "at", "family_id", "channel_label", "from_signal")} for c in today["contacts"][:6]
        ],
        "control": today["control"],
    }


def _state(ok: Optional[bool], warn: bool = False) -> str:
    """A node's colour: no record yet → idle; a failure → bad; something waiting → warn."""
    if ok is None:
        return "idle"
    return "bad" if not ok else "warn" if warn else "ok"


def admin(viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Vận hành (SCR-ADM-02): Hệ thống's own read (``app.web.system_read``) drawn as a map — sources, storage, AI,
    people — with the bell's alerts for Admin, the jobs failing, configuration waiting, people by role, the chain."""
    from app.web import system_read
    from control import alerts as control_alerts
    from control import config

    s = system_read()
    jobs = [j for j in s["jobs"] if j.get("last")]
    failing = [j for j in jobs if not j["last"]["ok"]]
    market = [j for j in jobs if j["id"].startswith("market_")]
    feeds_bad = [f for f in s["feeds"] if f.get("error")]
    runs = s["agent_runs"]
    agents_bad = [r for r in runs if r.get("last_status") not in (None, "ok")]
    up = s["availability"]
    pending = {k["pending"]["id"]: k for k in config.overview() if k.get("pending")}
    people = s["people"]
    from people import accounts as people_accounts

    waiting_accounts = sum(1 for r in people_accounts.requests() if r["status"] == "pending")
    roles_n: Dict[str, int] = {}
    for p in people:
        roles_n[p["role"]] = roles_n.get(p["role"], 0) + 1
    alerts = control_alerts.for_role("admin")  # what the bell holds for Admin: open and acknowledged
    zone = [a for a in alerts if a["kind"] in ("inbox", "zone_sync") and a["status"] == "open"]

    def node(id, lane, label, value, state, route, page, note="", error=None, items=None, at=None):
        return {"id": id, "lane": lane, "label": label, "value": value, "state": state, "route": route,
                "page": page, "note": note, "error": error, "items": items or [], "at": at}  # fmt: skip

    nodes = [
        node("feeds", "sources", "Nguồn tin", f"{len(s['feeds']) - len(feeds_bad)}/{len(s['feeds'])} nguồn",
             _state(not feeds_bad if s["feeds"] else None), "#/admin/he-thong", "Hệ thống",
             note="lấy gần nhất" if s.get("news_at") else "chưa lấy lần nào", at=s.get("news_at"),
             error="; ".join(f"{f['id']}: {f['error']}" for f in feeds_bad) or None,
             items=[{"title": f["id"], "sub": f"{f.get('accepted', 0)} tin nhận · {f.get('refused', 0)} từ chối",
                     "state": "bad" if f.get("error") else "ok"} for f in s["feeds"]]),
        node("market", "sources", "Dữ liệu thị trường",
             f"{sum(1 for j in market if j['last']['ok'])}/{len(market)} việc",
             _state(all(j["last"]["ok"] for j in market) if market else None), "#/admin/du-lieu", "Dữ liệu thị trường",
             error="; ".join(f"{j['id']}: {j['last']['error']}" for j in market if not j["last"]["ok"]) or None,
             items=[{"job": j["id"], "title": j["id"], "sub": "", "at": j["last"]["at"],
                     "state": "ok" if j["last"]["ok"] else "bad"} for j in market]),
        node("zone", "sources", "Vùng AI", f"{len(s['inbox'])} gói gần đây",
             _state(not zone) if (s["inbox"] or s["zone_syncs"] or zone) else "idle",
             "#/admin/he-thong", "Hệ thống", note=f"{len(s['zone_syncs'])} lần gửi gần đây",
             error="; ".join(a["title"] for a in zone) or None),
        node("schedule", "store", "Lịch chạy", f"{len(jobs) - len(failing)}/{len(jobs)} việc ổn",
             _state(not failing if jobs else None), "#/admin/he-thong", "Hệ thống",
             note=f"{len(s['jobs'])} việc khai báo, {len(jobs)} đã chạy",
             error="; ".join(f"{j['id']}: {j['last']['error']}" for j in failing) or None),
        node("chain", "store", "Chuỗi nhật ký", f"{s['chain']['count']} dòng",
             _state(s["chain"]["ok"] and s["worm"]["ok"]),
             "#/admin/nhat-ky", "Nhật ký", note="băm nối tiếp" + (" · chỉ-ghi-một-lần" if s["worm"]["on"] else ""),
             error=s["chain"].get("reason") or s["worm"].get("reason") or None),
        node("uptime", "store", "Sẵn sàng",
             f"{up['availability'] * 100:.2f}%".replace(".", ",") if up.get("availability") is not None else "chưa đo",
             _state(up.get("met") if up.get("availability") is not None else None), "#/admin/he-thong", "Hệ thống",
             note=f"mục tiêu {up['target'] * 100:.1f}% giờ làm việc".replace(".", ",")),
        node("agents", "ai", "Agent", {"live": "Mô hình thật", "mock": "Mô phỏng", "inbox": "Hộp chờ"}.get(
                 s["agents"]["mode"], s["agents"]["mode"]),
             _state(not agents_bad if runs else None), "#/admin/agent", "Agent",
             note=f"{sum(r['runs'] for r in runs)} lần chạy · {sum(r['failed'] for r in runs)} lỗi",
             error="; ".join(f"{r['agent']}: {r['last_error']}" for r in agents_bad) or None,
             items=[{"title": r["agent"], "sub": f"{r['runs']} lần · {r['failed']} lỗi", "at": r.get("last"),
                     "state": "ok" if r.get("last_status") == "ok" else "bad"} for r in runs]),
        node("queue", "ai", "Hàng đợi", f"{s['agent_queue']} yêu cầu",
             _state(True, warn=bool(s["agent_queue"] or s["evals_waiting"])), "#/admin/agent", "Agent",
             note=f"{len(s['evals_waiting'])} chờ bộ đánh giá"),
        node("people", "people", "Người dùng", f"{len(people)} nhân viên", _state(True, warn=bool(waiting_accounts)),
             "#/admin/tai-khoan", "Tài khoản và vai trò",
             note=f"{s['clients']} khách hàng"
             + (f" · {waiting_accounts} yêu cầu chờ duyệt" if waiting_accounts else "")),
        node("config", "people", "Cấu hình", f"{len(s['config_waiting'])} chờ duyệt",
             _state(True, warn=bool(s["config_waiting"])), "#/admin/cau-hinh", "Cấu hình",
             items=[{"title": c["label"], "sub": c["id"]} for c in s["config_waiting"]]),
    ]  # fmt: skip
    return {
        "role": "admin",
        "as_of": time.time(),
        "nodes": nodes,
        "alerts": alerts,
        "failing": [
            {
                "id": j["id"],
                "at": j["last"]["at"],
                "error": j["last"]["error"],
                "route": "#/admin/du-lieu" if j["id"].startswith("market_") else "#/admin/he-thong",
            }
            for j in failing
        ],  # fmt: skip
        "config": [
            {
                "id": c["id"],
                "label": c["label"],
                "by": pending[c["id"]]["pending"].get("proposed_by"),
                "two_person": bool(pending[c["id"]].get("two_person")),
            }
            for c in s["config_waiting"]
            if c["id"] in pending
        ],  # fmt: skip
        "evals": s["evals_waiting"],
        "roles": roles_n,
        "clients": s["clients"],
        "no_password": sum(1 for p in people if not p.get("has_password")),
        "account_requests": waiting_accounts,
        "chain": s["chain"],
        "worm": s["worm"],
    }


BUILD = {"cio": cio, "rm": rm, "admin": admin}


def desk(role: str, viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The desk of ``role``; a role without one (the client) is refused."""
    if role not in BUILD:
        raise roles.Forbidden(f"vai trò {role!r} không có bàn làm việc")
    return BUILD[role](viewer)

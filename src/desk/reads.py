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
    "specialist": "#/specialist",
    "compliance": "#/compliance",
}  # each role's desk address; a page's address is its menu id under it


def _late(job: Dict[str, Any]) -> bool:
    """A job failing now: its last error came after its last success (as Dữ liệu thị trường says it)."""
    return bool(job.get("last_error_at")) and (not job.get("last_ok") or job["last_error_at"] > job["last_ok"])


def _event_title(event_id: str) -> str:
    from events import store as events

    try:
        return events.get(event_id)["title"]
    except Exception:  # an event the store no longer has: its id says enough
        return event_id


def cio(viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Bàn quyết định (SCR-CIO-15): the news-to-family pipeline, what waits for the CIO's decision, the exposure of
    the latest effective run, the events, the model's data and the agents beneath the desk (FEAT-04, 05)."""
    from control import config
    from engine import default_model
    from events import store as events
    from market import factors as market_factors
    from market import store as market_store
    from measure import forecasts
    from news import store as news
    from newsletter import store as letters
    from views import ops as view_ops

    me = (viewer or {}).get("id") or "cio"
    names = {f.id: f.name for f in default_model().factors}

    fresh = news.inbox(status="new", limit=5000)
    high = [i for i in fresh if i.get("relevance") == "high"]

    evs = events.listing()
    states = []
    for ev in evs:
        vs = view_ops.event_views(ev["id"])
        latest = max(vs, key=lambda v: v["version"]) if vs else None
        states.append({"event": ev, "views": vs, "latest": latest})
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
                       "at": v["created"], "route": f"#/cio/nhan-dinh/{v['id']}"})  # fmt: skip
    for r in review:
        decide.append({"kind": "run", "id": r["id"], "title": _event_title(r["event_id"]), "status": r["status_label"],
                       "at": r["created"], "route": f"#/cio/ap-dung/{r['id']}"})  # fmt: skip
    for k in config.overview():
        p = k["pending"]
        if p and k["owner"] == "cio":
            mine = p.get("proposed_by") == me and k["two_person"]
            decide.append({"kind": "config", "id": p["id"], "title": k["label"],
                           "status": "Chờ một CIO khác duyệt" if mine else "Chờ CIO duyệt",
                           "at": p["created"], "route": "#/cio/cau-hinh"})  # fmt: skip
    for n in letters.listing():
        if n["status"] == "RETURNED":
            decide.append({"kind": "letter", "id": n["id"], "title": n.get("title") or n["id"],
                           "status": "Tuân thủ trả lại", "at": n["created"],
                           "route": f"#/cio/ban-tin/{n['id']}"})  # fmt: skip
    for s in no_view:
        ev = s["event"]
        decide.append({"kind": "event", "id": ev["id"], "title": ev["title"], "status": "Chưa có nhận định",
                       "at": ev["created"], "route": f"#/cio/nhan-dinh/{ev['id']}"})  # fmt: skip
    decide.sort(key=lambda x: -(x["at"] or 0))

    exposure = None
    if effective:
        r = effective[0]  # the newest effective run, as Phơi nhiễm opens it
        total = r["exposure"]["total"]
        top = sorted((f for f in total if total[f]), key=lambda f: -abs(total[f]))[:6]
        exposure = {
            "run_id": r["id"],
            "event": _event_title(r["event_id"]),
            "expected_3m": r["totals"]["expected_3m"],
            "families": r["families"],
            "pre_review": r["totals"]["pre_review"],
            "factors": [{"id": f, "name": names.get(f, f), "value": total[f]} for f in top],
            "worst": [
                {
                    "family_id": x["family_id"],
                    "name": x["name"],
                    "expected_3m_pct": x["expected_3m_pct"],
                    "pre_review": x["pre_review"],
                }
                for x in (r.get("ranking") or [])[:3]
            ],
            "route": f"#/cio/phoi-nhiem/{r['id']}",
        }

    factors = market_factors.factor_series()
    real = [
        f
        for f in factors
        if f.get("series") and f.get("months") is not None and not f["provenance"].startswith("Giả định")
    ]
    late = [{"job": j, "error": h.get("last_error")} for j, h in market_store.job_health().items() if _late(h)]
    rows = forecasts.all_rows()
    waiting = [x for x in rows if x.get("scored") is None]

    stage = lambda *a: dict(zip(("id", "label", "count", "unit", "waits", "note", "route"), a))  # noqa: E731
    pipeline = [
        stage("news", "Tin", len(fresh), "tin mới", len(high), f"{len(high)} liên quan cao", "#/cio/hop-tin"),
        stage("events", "Sự kiện", len(evs), "sự kiện", len(no_view) + len(held),
              f"{len(no_view)} chưa có nhận định" + (f" · {len(held)} bị giữ" if held else ""), "#/cio/nhan-dinh"),
        stage("views", "Nhận định", sum(len(s["views"]) for s in states), "phiên bản", len(waiting_views),
              f"{len(waiting_views)} chờ CIO duyệt", "#/cio/nhan-dinh"),
        stage("runs", "Lần áp dụng", len(effective), "đang hiệu lực", len(review) + len(computing),
              f"{len(review)} chờ CIO xem lại" + (f" · {len(computing)} đang tính" if computing else ""),
              "#/cio/ap-dung"),
        stage("families", "Gia đình", len(families), "gia đình được tính", len(flagged),
              f"{len(flagged)} chạm ngưỡng RM xem trước", "#/cio/phoi-nhiem"),
        stage("rm", "RM", len(rm_families), "gia đình RM cần xem trước", 0, "trên trang Hôm nay của RM",
              "#/cio/do-thi"),
    ]  # fmt: skip
    return {
        "role": "cio",
        "as_of": time.time(),
        "pipeline": pipeline,
        "decide": decide,
        "exposure": exposure,
        "events": [
            {"id": s["event"]["id"], "title": s["event"]["title"], "type": s["event"].get("type"),
             "status": s["latest"]["status"] if s["latest"] else None, "blocked": bool(s["event"].get("blocked")),
             "created": s["event"]["created"], "route": f"#/cio/nhan-dinh/{s['event']['id']}"}  # fmt: skip
            for s in sorted(states, key=lambda s: -s["event"]["created"])[:6]
        ],
        "model": {
            "factors_real": len(real),
            "factors": len(factors),
            "late_jobs": late,
            "forecasts": len(rows),
            "forecasts_waiting": len(waiting),
            "next_due": min((x["due"] for x in waiting), default=None),
        },
        "agents": view_ops.agent_status(),
        # what Thông tin lists for a stage picked on the pipeline (short; the page has the rest)
        "items": {
            "news": [{"id": i["id"], "title": i["title"], "sub": f"{i['outlet']} · {i.get('label') or ''}".strip(" ·"),
                      "route": "#/cio/hop-tin"} for i in high[:5]],
            "runs": [{"id": r["id"], "title": _event_title(r["event_id"]), "value": r["totals"]["expected_3m"],
                      "sub": f"{r['id']} · {r['families']} gia đình · {r['totals']['pre_review']} chạm ngưỡng",
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


def specialist(viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Bàn chuyên gia (SCR-SP-02): what Duyệt khuyến nghị reads (GET /api/review) — the recommendations an RM approved
    for a family assigned to this specialist, whose certificate is in force, waiting for them (BRD-RULE-ROLE-05,
    WF-08, G8); what they decided; their families. The family's picture beside a recommendation is read on the screen
    through the reads a specialist may already make (POST /api/dashboard, /api/goals; Q-26), not composed here."""
    from people import auth
    from people import store as people
    from review import specialist as sp
    from wealth import store as reviews

    v = viewer or {}
    me = v.get("id") if v.get("role") == "specialist" else None
    if v.get("families") is not None:
        fams = list(v["families"])
    elif me:
        fams = people.families_of_specialist(me)
    else:
        fams = people.client_ids()
    fams = auth.visible(sorted(fams))
    approves = {f for f in fams if any(a["id"] == me for a in sp.approvers(f))} if me else set()
    heads = {c: people.client(c).get("member_of") or c for c in people.client_ids(True)}
    rows = reviews.reviews()  # newest first
    waiting = [r for r in rows if r["status"] == "pending_specialist" and heads.get(r["client_id"]) in approves]
    decided = [r for r in rows if me and r["data"].get("specialist_by") == me]

    def item(r: Dict[str, Any]) -> Dict[str, Any]:
        d = r["data"]
        return {
            "id": r["id"], "family_id": heads.get(r["client_id"], r["client_id"]), "client_id": r["client_id"],
            "name": people.client(r["client_id"])["name"], "kind": r["kind"], "title": r["title"],
            "actions": list((d.get("option") or {}).get("actions") or []), "rm": d.get("decided_by"),
            "rm_note": r.get("note"), "status": r["status"], "created": r["created"], "decided": r.get("decided"),
            "note": d.get("specialist_note"),
        }  # fmt: skip

    def family(f: str) -> Dict[str, Any]:
        c = people.client(f)
        return {"id": f, "name": c["name"], "segment": c.get("segment"), "approves": f in approves,
                "waiting": sum(1 for r in waiting if heads.get(r["client_id"]) == f)}  # fmt: skip

    return {
        "role": "specialist",
        "as_of": time.time(),
        "me": me,
        "certificate": sp.certificate(me) if me else None,
        "families": [family(f) for f in fams],
        "waiting": [item(r) for r in reversed(waiting)],  # oldest first: it has waited longest
        "decided": [item(r) for r in decided[:8]],
    }


def compliance(viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Bàn kiểm soát (SCR-CMP-06): each control Compliance owns as a flow with what waits at each step — news held for
    the restricted list → released with a reason (BR-04); research waiting → released or rejected by another person
    after its release time (BR-03); letters waiting → approved or returned (FR-801); policy documents added → verified
    by a second person → summarised by the policy agent (FR-306); configuration waiting (FR-701); the audit chain
    (FR-702) — from the stores those pages read, and one queue of what waits for Compliance, oldest first."""
    from control import alerts as control_alerts
    from control import audit, config, db, worm
    from news import store as news
    from newsletter import store as letters
    from policy import store as policy
    from research import store as research

    now = time.time()
    items = news.inbox(status="all", limit=5000)
    held = [i for i in items if i["held"]]
    cleared = [i for i in items if i.get("cleared")]
    notes = research.listing()
    r_wait = [r for r in notes if r["status"] == "PENDING_RELEASE"]
    nls = letters.listing()
    l_wait = [n for n in nls if n["status"] == "PENDING_COMPLIANCE"]
    docs = policy.radar()["documents"]
    unverified = [d for d in docs if not d.get("verified") and d["status"] != "dropped"]
    verified = [d for d in docs if d.get("verified")]
    summarised = [d for d in verified if d.get("summary")]
    cfg = [k for k in config.overview() if k.get("pending")]
    with db.tx() as con:
        chain, copy = audit.verify(con), worm.verify(con)

    def step(label, count, waits=False):
        return {"label": label, "count": count, "waits": waits}

    def item(control, id, title, sub, at, route, ready=True):
        return {"control": control, "id": id, "title": title, "sub": sub, "at": at, "route": route, "ready": ready}

    def control(id, label, rule, page, steps, rows):
        return {"id": id, "label": label, "rule": rule, "route": f"#/compliance/{page[0]}", "page": page[1],
                "steps": steps, "items": rows}  # fmt: skip

    def research_item(r):
        early = "" if now >= r["release_at"] else " · chưa tới giờ phát hành"
        sub = f"{r.get('report_no') or r['kind']} · nạp bởi {r.get('uploaded_by') or '—'}{early}"
        ready = now >= r["release_at"]
        return item("research", r["id"], r["title"], sub, r["created"], "#/compliance/nghien-cuu", ready)

    def config_item(k):
        v = k["pending"]
        sub = f"đề xuất bởi {v.get('proposed_by') or '—'} · {k['owner_label']} duyệt"
        sub += " · cần người thứ hai" if k["two_person"] else ""
        return item("config", v["id"], k["label"], sub, (v.get("history") or [{}])[0].get("at") or now,
                    "#/compliance/cau-hinh")  # fmt: skip

    def held_item(i):
        sub = f"{i.get('outlet') or i.get('source')} · nhắc tới {', '.join(i.get('restricted') or [])}"
        return item("held", i["id"], i["title"], sub, i.get("published") or now, "#/compliance/giu")

    def letter_item(n):
        return item("letters", n["id"], n.get("title") or n["id"], f"soạn bởi {n.get('author') or '—'}", n["created"],
                    f"#/compliance/ban-tin/{n['id']}")  # fmt: skip

    def policy_item(x):
        sub = f"{policy.STATUS.get(x['status'], x['status'])} · thêm bởi {x.get('added_by') or '—'}"
        return item("policy", x["id"], x["title"], sub, x["created"], f"#/compliance/chinh-sach/{x['id']}")

    released = sum(r["status"] == "RELEASED" for r in notes)
    rejected = sum(r["status"] == "REJECTED" for r in notes)
    approved = sum(n["status"] == "APPROVED" for n in nls)
    returned = sum(n["status"] == "RETURNED" for n in nls)
    controls = [
        control("held", "Tin bị giữ", "BRD-BR-04", ("giu", "Tin bị giữ"),
                [step("Đang giữ", len(held), True), step("Đã cho phép", len(cleared))], [held_item(i) for i in held]),
        control("research", "Nghiên cứu", "BRD-BR-03", ("nghien-cuu", "Nghiên cứu"),
                [step("Chờ phát hành", len(r_wait), True), step("Đã phát hành", released), step("Từ chối", rejected)],
                [research_item(r) for r in r_wait]),
        control("letters", "Bản tin", "BRD-FR-801", ("ban-tin", "Bản tin"),
                [step("Chờ duyệt", len(l_wait), True), step("Đã duyệt", approved), step("Bị trả lại", returned)],
                [letter_item(n) for n in l_wait]),
        control("policy", "Chính sách", "BRD-FR-306", ("chinh-sach", "Chính sách"),
                [step("Chờ xác nhận", len(unverified), True), step("Đã xác nhận", len(verified)),
                 step("Đã tóm tắt", len(summarised))], [policy_item(x) for x in unverified]),
        control("config", "Cấu hình", "BRD-FR-701", ("cau-hinh", "Cấu hình"), [step("Chờ duyệt", len(cfg), True)],
                [config_item(k) for k in cfg]),
    ]  # fmt: skip
    queue = sorted((x for c in controls for x in c["items"]), key=lambda x: x["at"])
    return {
        "role": "compliance",
        "as_of": now,
        "controls": controls,
        "queue": queue,
        "chain": {
            "ok": chain["ok"],
            "count": chain["count"],
            "broken_at": chain.get("broken_at"),
            "reason": chain.get("reason"),
        },
        "worm": copy,
        "alerts": control_alerts.for_role("compliance"),
    }


BUILD = {"cio": cio, "rm": rm, "admin": admin, "specialist": specialist, "compliance": compliance}


def desk(role: str, viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The desk of ``role``; a role without one (the client) is refused."""
    if role not in BUILD:
        raise roles.Forbidden(f"vai trò {role!r} không có bàn làm việc")
    return BUILD[role](viewer)

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

ROUTE = {"cio": "#/cio"}  # each role's desk address; a page's address is its menu id under it


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


BUILD = {"cio": cio}


def desk(role: str, viewer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The desk of ``role``; a role without one (the client) is refused."""
    if role not in BUILD:
        raise roles.Forbidden(f"vai trò {role!r} không có bàn làm việc")
    return BUILD[role](viewer)

"""The monthly measurement reports (BRD §16.3, §15, §2; BRD_COMPLETION_PLAN F3), read from what the product records.

- **Misses (MEAS-03).** Important news (relevance “high”: our reading of “important”, Q-07) that never became an
  event, by cause: dismissed by the CIO, held for Compliance, or still in the inbox a day later. Events that did
  not reach families, by cause: no view, the view not approved (its status), or approved with no application run.
- **Rubber-stamping (MEAS-05).** For each approval: the CIO's time from the view being ready for approval to the
  approval, and whether the CIO approved it without an edit.
- **Speed (KPI-01, WF-09).** For each event that reached the RMs: from its earliest news being published to the
  application run being effective. Target ≤ 2 h. The BRD's “urgent ≤ 30 min” has no definition of urgent in the
  product (no news or event carries it), so it is not measured.
- **Agent and news timing (NFR-02).** News published → in the inbox (≤ 10 min), for news published after the
  ingest job was already running; each CIO agent run's duration (≤ 15 min).

Months are local (Asia/Ho_Chi_Minh, the server's zone).
"""

from __future__ import annotations

import json
import statistics
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from control import db
from news import store as news_store

DAY = 86400
KPI01_TARGET_H = 2.0
INBOX_TARGET_MIN = 10.0
AGENT_TARGET_MIN = 15.0
FAST_MIN = 2.0  # our signal, not a BRD threshold: an approval this quick is counted as “duyệt rất nhanh”


def _month(t: float) -> str:
    return datetime.fromtimestamp(t).strftime("%Y-%m")


def _rows(con, q: str, *args) -> List[Dict[str, Any]]:
    return [db.load(r) for r in con.execute(q, args)]


def _news_tables() -> None:
    """The news tables are the news store's (created on its first use; a new state file may not have them)."""
    with news_store._db():
        pass


def _stats(xs: List[float]) -> Dict[str, Any]:
    if not xs:
        return {"n": 0, "median": None, "p90": None, "max": None}
    s = sorted(xs)
    return {
        "n": len(s),
        "median": round(statistics.median(s), 2),
        "p90": round(s[min(len(s) - 1, int(0.9 * len(s)))], 2),
        "max": round(s[-1], 2),
    }


def misses(now: Optional[float] = None) -> Dict[str, Any]:
    now = now or time.time()
    _news_tables()
    with db.tx() as con:
        news = [
            dict(r) | {"data": json.loads(r["data"])}
            for r in con.execute(
                "select id, published, ingested, status, relevance, held, data from news_items where relevance = 'high'"
            )
        ]
        events = _rows(con, "select * from events")
        views = _rows(con, "select id, event_id, status, created, data from views")
        runs = _rows(con, "select id, view_id, event_id, status, created, data from application_runs")
    news_rows = []
    for n in news:
        if n["status"] in ("grouped", "refused"):
            continue
        if n["held"]:
            cause = "Giữ lại chờ Tuân thủ"
        elif n["status"] == "dismissed":
            note = next(
                (h.get("note") for h in reversed(n["data"].get("history", [])) if h["status"] == "dismissed"), ""
            )
            cause = "CIO bỏ qua" + (f": {note}" if note else "")
        elif now - n["ingested"] > DAY:
            cause = "Còn trong hộp tin quá 1 ngày"
        else:
            continue  # still fresh: not a miss yet
        news_rows.append(
            {"id": n["id"], "title": n["data"].get("title"), "month": _month(n["published"]), "cause": cause}
        )
    by_event_views: Dict[str, List[Dict[str, Any]]] = {}
    for v in views:
        by_event_views.setdefault(v["event_id"], []).append(v)
    run_views = {r["view_id"] for r in runs if r["status"] == "EFFECTIVE"}
    event_rows = []
    for e in events:
        vs = by_event_views.get(e["id"], [])
        if any(v["id"] in run_views for v in vs):
            continue
        if not vs:
            cause = "Chưa có nhận định"
        elif any(v["status"] == "APPROVED" for v in vs):
            cause = "Đã duyệt nhưng chưa có lượt áp dụng hiệu lực"
        else:
            cause = f"Nhận định chưa được duyệt ({vs[-1]['status']})"
        if now - e["created"] < DAY and cause != "Đã duyệt nhưng chưa có lượt áp dụng hiệu lực":
            continue  # under a day old and still moving
        event_rows.append({"id": e["id"], "title": e.get("title"), "month": _month(e["created"]), "cause": cause})
    return {"news": news_rows, "events": event_rows, "by_month": _count_by_month(news_rows, event_rows)}


def _count_by_month(news_rows, event_rows) -> List[Dict[str, Any]]:
    months = sorted({r["month"] for r in news_rows + event_rows})
    out = []
    for m in months:
        causes: Dict[str, int] = {}
        for r in news_rows + event_rows:
            if r["month"] == m:
                key = r["cause"].split(":")[0]
                causes[key] = causes.get(key, 0) + 1
        out.append(
            {
                "month": m,
                "news": sum(1 for r in news_rows if r["month"] == m),
                "events": sum(1 for r in event_rows if r["month"] == m),
                "causes": causes,
            }
        )
    return out


def rubber_stamp() -> Dict[str, Any]:
    with db.tx() as con:
        views = _rows(con, "select id, event_id, status, created, data from views")
    rows = []
    for v in views:
        hist = v.get("history", [])
        app = next((i for i in range(len(hist) - 1, -1, -1) if hist[i]["status"] == "APPROVED"), None)
        if app is None:
            continue
        ready = next((hist[i]["at"] for i in range(app - 1, -1, -1) if hist[i]["status"] == "PENDING_APPROVAL"), None)
        rows.append(
            {
                "id": v["id"],
                "month": _month(hist[app]["at"]),
                "by": hist[app].get("by"),
                "minutes": round((hist[app]["at"] - ready) / 60, 2) if ready else None,
                "edited": bool(v.get("edits")),
            }
        )
    months = []
    for m in sorted({r["month"] for r in rows}):
        mine = [r for r in rows if r["month"] == m]
        mins = [r["minutes"] for r in mine if r["minutes"] is not None]
        months.append(
            {
                "month": m,
                "approved": len(mine),
                "minutes": _stats(mins),
                "no_edit_share": round(sum(1 for r in mine if not r["edited"]) / len(mine), 3),
                "fast": sum(1 for x in mins if x < FAST_MIN),
            }
        )
    return {"views": rows, "by_month": months, "fast_minutes": FAST_MIN}


def speed() -> Dict[str, Any]:
    _news_tables()
    with db.tx() as con:
        events = {e["id"]: e for e in _rows(con, "select * from events")}
        runs = _rows(con, "select id, view_id, event_id, status, created, data from application_runs")
        news = {r["id"]: r["published"] for r in con.execute("select id, published from news_items")}
    rows = []
    for r in runs:
        eff = next((h["at"] for h in r.get("history", []) if h.get("status") == "EFFECTIVE"), None)
        e = events.get(r["event_id"])
        if eff is None or e is None:
            continue
        pub = [news[i] for i in e.get("news_ids", []) if i in news]
        if not pub:
            continue
        hours = (eff - min(pub)) / 3600
        rows.append(
            {
                "run": r["id"],
                "event_id": e["id"],
                "month": _month(eff),
                "hours": round(hours, 2),
                "met": hours <= KPI01_TARGET_H,
            }
        )
    months = []
    for m in sorted({x["month"] for x in rows}):
        mine = [x for x in rows if x["month"] == m]
        months.append(
            {
                "month": m,
                "hours": _stats([x["hours"] for x in mine]),
                "met_share": round(sum(x["met"] for x in mine) / len(mine), 3),
            }
        )
    return {"runs": rows, "by_month": months, "target_hours": KPI01_TARGET_H, "urgent": "chưa có định nghĩa"}


def timing() -> Dict[str, Any]:
    _news_tables()
    with db.tx() as con:
        first_run = con.execute("select min(at) from news_runs").fetchone()[0]
        lags = [
            (r["published"], (r["ingested"] - r["published"]) / 60)
            for r in con.execute("select published, ingested from news_items")
            if first_run is not None and r["published"] >= first_run
        ]
        agents = _rows(con, "select id, agent, subject_id, created, data from agent_runs where agent = 'cio'")
    lag_months = []
    for m in sorted({_month(p) for p, _ in lags}):
        xs = [max(lag, 0.0) for p, lag in lags if _month(p) == m]
        lag_months.append(
            {"month": m, "minutes": _stats(xs), "met_share": round(sum(x <= INBOX_TARGET_MIN for x in xs) / len(xs), 3)}
        )
    runs = [
        {
            "id": a["id"],
            "view_id": a["subject_id"],
            "month": _month(a["created"]),
            "status": a.get("status"),
            "minutes": round((a["finished"] - a["created"]) / 60, 2),
        }
        for a in agents
        if a.get("finished")
    ]
    agent_months = []
    for m in sorted({r["month"] for r in runs}):
        xs = [r["minutes"] for r in runs if r["month"] == m]
        agent_months.append(
            {"month": m, "minutes": _stats(xs), "met_share": round(sum(x <= AGENT_TARGET_MIN for x in xs) / len(xs), 3)}
        )
    return {
        "inbox": {"by_month": lag_months, "target_minutes": INBOX_TARGET_MIN, "since": first_run},
        "agent": {"runs": runs, "by_month": agent_months, "target_minutes": AGENT_TARGET_MIN},
    }


def all_reports() -> Dict[str, Any]:
    return {"misses": misses(), "rubber_stamp": rubber_stamp(), "speed": speed(), "timing": timing()}

"""The collection monitor (AGENT_EVALUATION_PLAN §2.1): each ingest run's funnel and health, and the days' trends.

Runs come from ``news_runs`` (one per 10-minute ingest). Runs recorded before 2026-10-24 kept fewer fields: what
can be worked out from what they kept (fetched, skipped, sources, status) is; the rest (start and end, configured
sources, relevant, groups, missing metadata) is None, never 0. A day's item counts (unique, retained, relevant,
groups) come from the items themselves by **collection** time (``ingested``), the same for every day; publication
time is kept apart and only used for the lag.

A day's collection time (NEWS_OPS_PLAN N2) is the sum of its runs' own durations, over the runs that kept one, with
their count beside it. A news item reached a portfolio (N3) when its event has an application run the RMs see with at
least one family whose expected 3-month change is not zero; the count grows after the day, as views are approved.
"""

from __future__ import annotations

import json
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from news import store
from news.ops import NO_TIME
from trial import segments

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
CATEGORIES = (*segments.FAMILIES, "unclassified")


def day_of(t: float) -> str:
    return datetime.fromtimestamp(t, TZ).date().isoformat()


def _start_of(day: str) -> float:
    return datetime.fromisoformat(day).replace(tzinfo=TZ).timestamp()


def normalise(run: Dict[str, Any]) -> Dict[str, Any]:
    """A run in today's shape. A field an old run did not keep is None; what its sources say is filled in."""
    src = run.get("sources") or {}
    failed = sorted(sid for sid, c in src.items() if c.get("error"))
    attempted = len(src)
    derived = {
        "fetched": sum(int(c.get("fetched") or 0) for c in src.values()),
        "skipped": sum(int(c.get("skipped") or 0) for c in src.values()),
        "attempted": attempted,
        "failed": len(failed),
        "succeeded": attempted - len(failed),
        "failed_sources": {sid: src[sid]["error"] for sid in failed},
        "status": "failed" if attempted == 0 or len(failed) == attempted else "partial" if failed else "ok",
        "retained": run.get("added"),
        "unique": (run["added"] + run["refused"]) if "added" in run and "refused" in run else None,
    }
    out = {k: None for k in ("started", "finished", "duration_s", "configured", "relevant", "by_category", "missing")}
    out.update(derived)
    out.update({k: v for k, v in run.items() if v is not None or k not in derived})
    out["full"] = "started" in run  # recorded with the monitor's fields
    return out


def runs(since: float, until: Optional[float] = None) -> List[Dict[str, Any]]:
    until = until or time.time()
    with store._db() as con:
        rows = con.execute(
            "select id, data from news_runs where at >= ? and at < ? order by at", (since, until)
        ).fetchall()
    return [{"id": r["id"], **normalise(json.loads(r["data"]))} for r in rows]


def _items(since: float, until: float) -> List[Dict[str, Any]]:
    with store._db() as con:
        rows = con.execute("select * from news_items where ingested >= ? and ingested < ?", (since, until)).fetchall()
    return [store._item(r) for r in rows]


def reached() -> Dict[str, set]:
    """Each news item that reached a portfolio, and the families it reached (N3)."""
    from apply import run as apply_run
    from control import db

    fams: Dict[str, set] = defaultdict(set)
    for r in apply_run.runs(statuses=apply_run.RM_VISIBLE):
        hit = {f["family_id"] for f in r.get("ranking") or [] if f.get("expected_3m")}
        if hit:
            fams[r["event_id"]] |= hit
    if not fams:
        return {}
    with db.tx() as con:
        rows = con.execute(f"select * from events where id in ({','.join('?' * len(fams))})", list(fams)).fetchall()
    out: Dict[str, set] = defaultdict(set)
    for row in rows:
        ev = db.load(row)
        for nid in ev.get("news_ids") or []:
            out[nid] |= fams[ev["id"]]
    return dict(out)


def _relevant(item: Dict[str, Any]) -> bool:
    return item.get("relevance") in ("high", "medium") and not item.get("restricted")


def _sum(rs: List[Dict[str, Any]], key: str) -> Optional[int]:
    """The runs' total, or None when any run did not keep it (a partial total would read as a fall)."""
    vals = [r.get(key) for r in rs]
    return None if not vals or any(v is None for v in vals) else int(sum(vals))


def days(n: int = 14, now: Optional[float] = None) -> List[Dict[str, Any]]:
    """The last ``n`` collection days (Vietnam time), newest first: the runs' funnel and health, the items kept."""
    now = now or time.time()
    today = day_of(now)
    first = _start_of(today) - (n - 1) * 86400
    by_run: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in runs(first, now + 1):
        by_run[day_of(r["at"])].append(r)
    by_item: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    reach = reached()
    for it in _items(first, now + 1):
        by_item[day_of(it["ingested"])].append(it)
    out = []
    for k in range(n):
        day = day_of(first + k * 86400 + 3600)
        rs, items = by_run.get(day, []), by_item.get(day, [])
        kept = [i for i in items if i["status"] != "refused"]
        lag = [(i["ingested"] - i["published"]) / 60 for i in kept if i.get("published")]
        cats = Counter(segments.family_of_item(i) or "unclassified" for i in kept)
        status = Counter(r["status"] for r in rs)
        timed = [r["duration_s"] for r in rs if r.get("duration_s") is not None]
        hit = [reach[i["id"]] for i in kept if i["id"] in reach]
        out.append(
            {
                "day": day,
                "runs": len(rs),
                "runs_ok": status["ok"],
                "runs_partial": status["partial"],
                "runs_failed": status["failed"],
                "source_failures": sum(r["failed"] for r in rs),
                "fetched": _sum(rs, "fetched") if rs else None,
                "skipped": _sum(rs, "skipped") if rs else None,
                "duplicates": _sum(rs, "duplicates") if rs else None,
                "unique": len(items),
                "refused": len(items) - len(kept),
                "retained": len(kept),
                "relevant": sum(1 for i in kept if _relevant(i)),
                "held": sum(1 for i in kept if i.get("restricted")),
                "by_category": {c: cats[c] for c in CATEGORIES},
                "missing": {
                    "published": sum(1 for i in items if i.get("refused_reason") == NO_TIME),
                    "summary": sum(1 for i in kept if not (i.get("summary") or "").strip()),
                    "category": cats["unclassified"],
                },
                "lag_min_p50": round(statistics.median(lag), 1) if lag else None,
                "duration_s_p50": _median(timed),
                "duration_s_total": round(sum(timed), 1) if timed else None,
                "duration_runs": len(timed),  # the runs that kept their duration (runs from 2026-10-24)
                "first_run": min((r.get("started") or r["at"] for r in rs), default=None),
                "last_run": max((r.get("finished") or r["at"] for r in rs), default=None),
                "portfolio": len(hit),
                "portfolio_families": len(set().union(*hit)) if hit else 0,
            }
        )
    return out[::-1]


def _median(xs: List[float]) -> Optional[float]:
    return round(statistics.median(xs), 2) if xs else None


def sources(since: float, until: Optional[float] = None) -> List[Dict[str, Any]]:
    """Per source over the window: runs attempted and failed, items fetched, the last error."""
    acc: Dict[str, Dict[str, Any]] = {}
    for r in runs(since, until):
        for sid, c in (r.get("sources") or {}).items():
            a = acc.setdefault(sid, {"source": sid, "attempted": 0, "failed": 0, "fetched": 0, "last_error": None})
            a["attempted"] += 1
            a["fetched"] += int(c.get("fetched") or 0)
            if c.get("error"):
                a["failed"] += 1
                a["last_error"] = {"at": r["at"], "error": c["error"]}
    return sorted(acc.values(), key=lambda a: (-a["failed"], a["source"]))


def summary(n: int = 14, now: Optional[float] = None) -> Dict[str, Any]:
    """View A of the trial page: the last run, the days, the sources over the days, and when the monitor began."""
    now = now or time.time()
    ds = days(n, now)
    since = _start_of(ds[-1]["day"])
    with store._db() as con:
        last = con.execute("select id, data from news_runs order by at desc, id desc limit 1").fetchone()
        full = con.execute("select min(at) from news_runs where data like '%\"started\"%'").fetchone()[0]
    return {
        "at": now,
        "last_run": {"id": last["id"], **normalise(json.loads(last["data"]))} if last else None,
        "days": ds,
        "sources": sources(since, now + 1),
        "full_since": full,  # runs from here keep every field; before, some are None (unavailable)
        "categories": {**segments.FAMILIES, "unclassified": "Chưa xếp"},
    }

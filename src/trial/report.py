"""The trial's report (B1.6): what the business asked to see, from the stored rows — collection, recall, speed, the
agents' runs, and their shadow forecasts' accuracy overall, per segment, per factor and per horizon, the buy/sell
readings and the scenarios. Every share comes with its count: a week of mornings is a small sample, and says so."""

from __future__ import annotations

import statistics
import time
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

from engine import default_model
from news import reference
from news import store as news_store
from trial import daily, segments, shadow

MIN_CALLED = 3  # factors scored with a direction before a draft's scenario can be judged at a horizon


def _share(hits: int, n: int) -> Optional[float]:
    return round(hits / n, 3) if n else None


def _median(xs: List[float]) -> Optional[float]:
    return round(statistics.median(xs), 1) if xs else None


def collection(since: float, until: float) -> Dict[str, Any]:
    """The news collected in the window: per day, per segment, per region, per source, how much had a type."""
    with news_store._db() as con:
        q = "select * from news_items where status != 'refused' and published >= ? and published < ?"
        items = [news_store._item(r) for r in con.execute(q, (since, until))]
    lag = [(i["ingested"] - i["published"]) / 60
           for i in items if i.get("published") and i["ingested"] >= i["published"]]
    by_day = Counter(datetime.fromtimestamp(i["published"]).date().isoformat() for i in items)
    return {
        "items": len(items),
        "per_day": dict(sorted(by_day.items())),
        "typed": len([i for i in items if i.get("event_type")]),
        "by_segment": dict(Counter(segments.of_item(i) or "none" for i in items)),
        "by_region": dict(Counter(i.get("kind") or "none" for i in items)),
        "by_source": dict(Counter(i["source"] for i in items).most_common()),
        "by_relevance": dict(Counter(i.get("relevance") or "none" for i in items)),
        "ingest_lag_min_p50": _median(lag),
    }


def recall(since: float) -> Dict[str, Any]:
    """KPI-02 from the independent reference (news/reference.py), for the trial's days."""
    cov = reference.coverage()
    day0 = datetime.fromtimestamp(since).date().isoformat()
    mine = [d for d in cov["by_day"] if d["period"] >= day0]
    important = sum(d["important"] for d in mine)
    collected = sum(d["collected"] for d in mine)
    return {
        "important": important,
        "collected": collected,
        "share": _share(collected, important),
        "target": cov["target"],
        "by_day": mine,
        "misses": [m for m in cov["misses"] if m["at"] >= since][:10],
    }


def runs(trials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The agents' events: made, drafts that reached the CIO, errors, and how long each step took."""
    ok = [t for t in trials if t.get("status") in shadow.RECORDED]
    first = [(t["created"] - t["first_published"]) / 3600 for t in trials if t.get("first_published")]
    return {
        "events": len(trials),
        "drafts": len(ok),
        "errors": [{"event_id": t["event_id"], "error": t.get("error")} for t in trials if t not in ok],
        "by_segment": dict(Counter(t.get("segment") or "none" for t in trials)),
        "agent_s_p50": _median([t["agent_s"] for t in trials if t.get("agent_s")]),
        "agent_s_max": max((t["agent_s"] for t in trials if t.get("agent_s")), default=None),
        "group_s_p50": _median([t["group_s"] for t in trials if t.get("group_s")]),
        "news_to_event_h_p50": _median(first),
    }


def _accuracy(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    scored = [r for r in rows if r.get("result") == "scored"]
    called = [r for r in scored if r.get("direction_hit") is not None]
    return {
        "kept": len(rows),
        "pending": sum(1 for r in rows if r.get("scored") is None),
        "n": len(scored),
        "coverage": _share(sum(1 for r in scored if r["inside"]), len(scored)),
        "direction_n": len(called),
        "direction_right": sum(1 for r in called if r["direction_hit"]),
        "direction_hit": _share(sum(1 for r in called if r["direction_hit"]), len(called)),
    }


def _call_right(r: Dict[str, Any], edge: float) -> bool:
    x = r["realised"]
    return x > 0 if r["call"] == "mua" else x < 0 if r["call"] == "bán" else abs(x) <= edge


def calls(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The buy/sell readings, per asset and horizon: how many of each, and how many the market bore out."""
    m = shadow.model()
    out: Dict[str, Any] = {}
    for h in shadow.HORIZON_DAYS:
        for fid, label in shadow.CALLS.items():
            mine = [r for r in rows if r["horizon"] == h and r["factor"] == fid and r.get("call")]
            done = [r for r in mine if r.get("result") == "scored"]
            edge = shadow.CALL_SHARE * m.factor(fid).vol_month * (m.horizons[h] ** 0.5)
            right = [r for r in done if _call_right(r, edge)]
            out.setdefault(h, []).append(
                {
                    "factor": fid,
                    "label": label,
                    "calls": dict(Counter(r["call"] for r in mine)),
                    "n": len(done),
                    "right": len(right),
                    "share": _share(len(right), len(done)),
                }
            )
    return out


def scenarios(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Per draft and horizon: the scenario the market took (the one whose path agreed in sign with the most scored
    factors) against the one the agents rated most likely."""
    by: Dict[tuple, List[Dict[str, Any]]] = {}
    for r in rows:
        if r.get("result") == "scored" and r.get("realised"):
            by.setdefault((r["view_id"], r["horizon"]), []).append(r)
    out: Dict[str, Dict[str, int]] = {}
    for (vid, h), rs in by.items():
        branches = rs[0].get("branches") or []
        if len(branches) < 2:
            continue
        agree = Counter()
        n = 0
        for r in rs:
            paths = {b["id"]: b["expected"] for b in r.get("branches") or []}
            if not any(paths.values()):
                continue
            n += 1
            for bid, exp in paths.items():
                if exp and (exp > 0) == (r["realised"] > 0):
                    agree[bid] += 1
        if n < MIN_CALLED:
            continue
        top = max(agree.values(), default=0)
        took = {b for b, k in agree.items() if k == top}
        likely = max(branches, key=lambda b: b["p"])["id"]
        mine = out.setdefault(h, {"judged": 0, "main_taken": 0, "tied": 0})
        mine["judged"] += 1
        mine["main_taken"] += int(likely in took)
        mine["tied"] += int(len(took) > 1)
    for v in out.values():
        v["share"] = _share(v["main_taken"], v["judged"])
    return out


def summary(now: Optional[float] = None) -> Dict[str, Any]:
    now = now or time.time()
    by_day = daily.days()
    trials = [t for ts in by_day.values() for t in ts]
    since = min((t["created"] for t in trials), default=now) - daily.WINDOW_S
    rows = shadow.rows()
    names = {f.id: f.name for f in default_model().factors}
    accuracy = {}
    for h in shadow.HORIZON_DAYS:
        mine = [r for r in rows if r["horizon"] == h]
        accuracy[h] = {
            **_accuracy(mine),
            "uncalibrated": h in shadow.UNCALIBRATED,
            "next_due": min((r["due"] for r in mine if r.get("scored") is None), default=None),
            "by_segment": {s: _accuracy([r for r in mine if r.get("segment") == s]) for s in segments.SEGMENTS},
            "by_region": {g: _accuracy([r for r in mine if r.get("region") == g]) for g in segments.REGIONS},
            "by_factor": [{"id": f, "name": names.get(f, f), **_accuracy([r for r in mine if r["factor"] == f])}
                          for f in names if any(r["factor"] == f for r in mine)],
        }
    return {
        "at": now,
        "days": sorted(by_day),
        "collection": collection(since, now),
        "recall": recall(since),
        "runs": runs(trials),
        "accuracy": accuracy,
        "calls": calls(rows),
        "scenarios": scenarios(rows),
        "events": [{k: t.get(k) for k in ("day", "event_id", "title", "segment", "region", "view_id", "status",
                                          "error", "agent_s")} for t in trials],
        "segments": segments.SEGMENTS,
        "regions": segments.REGIONS,
    }

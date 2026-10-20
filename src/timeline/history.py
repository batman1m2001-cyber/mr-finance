"""A person's simulated money history (data/history/<person>.json, written by scripts/make_history.py; plan:
docs/NODE_TIMELINE_PLAN.md).

Each file holds one grid of dates (month-ends from 2020-12-31, then every day of the last year to the demo date),
each of today's holdings on it, the money that was elsewhere before it bought them (``closed``: a deposit since
closed), and the person's transactions before the fixtures' twelve months. A holding the file does not know (one
declared or uploaded in the app since) is flat at its month-ago value, then moves to today's over the last month —
as Tổng quan counts it."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from wealth.paths import DATA

START = date(2020, 12, 31)
DAILY_FROM = date(2025, 10, 1)  # the fixtures' first transaction month: every day from here
_cache: Dict[str, tuple] = {}


def day(s: str) -> date:
    return date.fromisoformat(s[:10])


def month_back(d: date) -> date:
    """The same day a month before (the 28th or 30th at most): where a holding's ``prev_value`` is."""
    y, m = (d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)
    return date(y, m, min(d.day, 28 if m == 2 else 30))


def year_back(d: date) -> date:
    return date(d.year - 1, d.month, min(d.day, 28) if d.month == 2 else d.day)


def grid(as_of: date) -> List[date]:
    """Month-ends from 2020-12-31 until the daily window, then every day to the demo date."""
    out, y, m = [], START.year, START.month
    while True:
        nxt = date(y + (m == 12), m % 12 + 1, 1)
        end = nxt - timedelta(days=1)
        if end >= DAILY_FROM:
            break
        out.append(end)
        y, m = nxt.year, nxt.month
    d = DAILY_FROM
    while d <= as_of:
        out.append(d)
        d += timedelta(days=1)
    return out


def load(person: str) -> Optional[Dict[str, Any]]:
    """One person's file, read once per change on disk; None when there is none."""
    path = DATA / "history" / f"{person}.json"
    try:
        stamp = path.stat().st_mtime_ns
    except OSError:
        return None
    hit = _cache.get(person)
    if hit and hit[0] == stamp:
        return hit[1]
    doc = json.loads(path.read_text(encoding="utf-8"))
    _cache[person] = (stamp, doc)
    return doc


class Book:
    """The series of a picture's holdings (and the people's closed deposits) on one grid of dates."""

    def __init__(self, holdings: List[Dict[str, Any]], people: List[str], as_of: str):
        self.as_of = day(as_of)
        files = {p: load(p) for p in people}
        known = [f for f in files.values() if f and f["as_of"] == as_of]
        self.dates = [day(d) for d in known[0]["dates"]] if known else grid(self.as_of)
        self.at = {d: i for i, d in enumerate(self.dates)}
        self.simulated = bool(known)
        t1 = month_back(self.as_of)
        self.rows: List[Dict[str, Any]] = []
        self.items: List[Dict[str, Any]] = []  # {key, class, kind, values}
        stored: Dict[str, List[float]] = {}
        for p, f in files.items():
            if not f or f["as_of"] != as_of:
                continue
            for k, s in f["holdings"].items():
                stored[k] = s["values"]
            for k, s in f["closed"].items():
                self.items.append({"key": k, "class": s["class"], "kind": s["kind"], "name": s["name"],
                                   "closed": True, "liquid": True, "values": s["values"]})  # fmt: skip
            self.rows += [{**r, "owner": p} for r in f.get("transactions", [])]
        for h in holdings:
            v = stored.get(h["key"])
            if v is None or len(v) != len(self.dates) or abs(v[-1] - h["value"]) > max(1_000, 0.005 * abs(h["value"])):
                prev, now = float(h["prev_value"]), float(h["value"])
                span = max(1, (self.as_of - t1).days)
                v = [prev if d <= t1 else prev + (now - prev) * (d - t1).days / span for d in self.dates]
            self.items.append({**h, "closed": False, "values": v})

    def value(self, items: List[Dict[str, Any]], d: date, net: bool = False) -> float:
        """The sum of ``items`` on ``d`` (the grid's last date on or before it); ``net``: debts subtract."""
        i = self.index(d)
        return sum((-1 if net and x["kind"] == "liability" else 1) * x["values"][i] for x in items)

    def index(self, d: date) -> int:
        if d in self.at:
            return self.at[d]
        best = 0
        for i, x in enumerate(self.dates):
            if x > d:
                break
            best = i
        return best

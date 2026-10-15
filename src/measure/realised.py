"""What a factor did between two days, in its unit, from the stored series (FEAT-35) — what a forecast is scored
against.

- ``pct``: the level's percentage change; ``bp``: the yield's change in %, ×100; ``pp``: the gap's change.
- ``sd`` (FOREIGN_FLOW): the net buying over the period, less the average month's times the months, over the
  standard deviation of the monthly sums — the monthly z-score of ``market.factors.moves`` summed over the period.

A level is the last point on or before the day, and only if it is at most ``STALE_DAYS`` old: a day the series
had no point (a holiday) takes the one before it; a gap longer than that is no data.
"""

from __future__ import annotations

import bisect
import math
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from market import factors as mf
from market import fetch

STALE_DAYS = 7
DAYS_PER_MONTH = 365.25 / 12
Point = Tuple[str, float]


class Series:
    """One factor's daily points and the unit its moves are measured in."""

    def __init__(self, factor: str, unit: str, points: List[Point]):
        self.factor, self.unit = factor, unit
        self.days = [d for d, _ in points]
        self.vals = [v for _, v in points]
        if unit == "sd":
            sums = mf.month_sums(points)
            xs = [v for _, v in sums]
            self.mean = sum(xs) / len(xs) if xs else 0.0
            self.sd = math.sqrt(sum((x - self.mean) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 2 else 0.0

    @property
    def first(self) -> Optional[str]:
        return self.days[0] if self.days else None

    @property
    def last(self) -> Optional[str]:
        return self.days[-1] if self.days else None

    def level(self, day: str) -> Optional[float]:
        i = bisect.bisect_right(self.days, day) - 1
        if i < 0 or (date.fromisoformat(day) - date.fromisoformat(self.days[i])).days > STALE_DAYS:
            return None
        return self.vals[i]

    def move(self, d0: str, d1: str) -> Optional[float]:
        """The factor's move from the end of ``d0`` to the end of ``d1``; None without data at both ends."""
        if not self.days or d1 > self.last or d0 < self.first:
            return None
        if self.unit == "sd":
            if not self.sd:
                return None
            i, j = bisect.bisect_right(self.days, d0), bisect.bisect_right(self.days, d1)
            months = (date.fromisoformat(d1) - date.fromisoformat(d0)).days / DAYS_PER_MONTH
            return (sum(self.vals[i:j]) - self.mean * months) / self.sd
        v0, v1 = self.level(d0), self.level(d1)
        if v0 is None or v1 is None:
            return None
        if self.unit == "pct":
            return (v1 / v0 - 1) * 100 if v0 else None
        if self.unit == "bp":
            return (v1 - v0) * 100
        return v1 - v0


def series() -> Dict[str, Series]:
    """Every data-backed factor of the model in force (the assumed ones have nothing to score against)."""
    back = mf.backing()
    assumed = set(fetch.catalogue().get("assumed") or [])
    out = {}
    for f in mf._model_factors():
        b = back.get(f["id"])
        if b is None or f["id"] in assumed:
            continue
        pts = mf.values(b["series"])
        if pts:
            out[f["id"]] = Series(f["id"], f["unit"], pts)
    return out


def add_days(day: str, n: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=n)).isoformat()

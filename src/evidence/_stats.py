"""The statistics branch (NEWS_EVIDENCE_BRD §5): what a series did after each precedent, against any window of the
same length. Computed, never written by a model."""

from __future__ import annotations

from datetime import date, timedelta
from statistics import median
from typing import Any, Dict, List, Sequence, Tuple

from evidence import catalogue as cat

DAYS = {"1w": 7, "1m": 30, "3m": 91}


def _after(points: Sequence[Tuple[str, float]], i: int, days: int) -> int:
    """The index of the first point at least ``days`` after point ``i``, or -1."""
    end = (date.fromisoformat(points[i][0]) + timedelta(days=days)).isoformat()
    for j in range(i + 1, len(points)):
        if points[j][0] >= end:
            return j
    return -1


def _start(points: Sequence[Tuple[str, float]], day: str) -> int:
    """The last close on or before ``day``: the market before the news (a Fed decision lands overnight, Vietnam time)."""
    i = -1
    for k, (d, _) in enumerate(points):
        if d > day:
            break
        i = k
    return i


def measure(points: Sequence[Tuple[str, float]], events: List[str], timeframe: str = "1w") -> Dict[str, Any]:
    """n, the moves after each event, how many went each way, the base rate of the same way over every window of the
    same length, the median and the range, the period, and the direction (§5, N5). ``points``: (date, close), sorted."""
    days = DAYS[timeframe]
    moves = []
    for e in sorted(events):
        i = _start(points, e)
        j = _after(points, i, days) if i >= 0 else -1
        if i >= 0 and j >= 0:
            moves.append({"date": e, "change": points[j][1] / points[i][1] - 1})
    base = [points[j][1] / points[i][1] - 1 for i in range(len(points)) if (j := _after(points, i, days)) >= 0]
    n = len(moves)
    down = sum(1 for m in moves if m["change"] < 0)
    up = n - down
    out: Dict[str, Any] = {
        "n": n,
        "timeframe": timeframe,
        "timeframe_label": cat.TIMEFRAMES[timeframe],
        "moves": [{**m, "change": round(m["change"], 4)} for m in moves],
        "period": [points[0][0][:4], points[-1][0][:4]] if points else None,
        "enough": n >= cat.MIN_PRECEDENTS,
    }
    if not n or not base:
        return {**out, "direction": "unclear"}
    way = "down" if down >= up else "up"
    same = down if way == "down" else up
    base_rate = sum(1 for b in base if (b < 0 if way == "down" else b >= 0)) / len(base)
    edge = same / n - base_rate
    changes = [m["change"] for m in moves]
    return {
        **out,
        "way": way,
        "same": same,
        "rate": same / n,
        "base_rate": round(base_rate, 4),
        "edge": round(edge, 4),
        "median": round(median(changes), 4),
        "low": round(min(changes), 4),
        "high": round(max(changes), 4),
        "direction": ("negative" if way == "down" else "positive") if out["enough"] and edge >= cat.MIN_EDGE else "unclear",
    }


def sentence(s: Dict[str, Any], event: str, series: str) -> str:
    """§5's sentence: n and the base rate always, never a percentage alone."""
    if not s["n"]:
        return f"Chưa đo được lần {event} nào trên {series}."
    word = "giảm" if s["way"] == "down" else "tăng"
    pc = lambda x: f"{x * 100:+.1f}%".replace(".", ",").replace("-", "−")  # noqa: E731
    return (
        f"Trong {s['n']} lần {event} từ {s['period'][0]}, {series} {word} trong {s['timeframe_label']} sau đó "
        f"{s['same']} lần ({s['rate']:.0%}), so với {s['base_rate']:.0%} ở {s['timeframe_label']} bất kỳ. "
        f"Trung vị {pc(s['median'])}, dao động {pc(s['low'])} đến {pc(s['high'])}."
    )

"""The forecast lab (FORECAST_DESK_PLAN step 1): any track of forecasts on a replay's moves, scored by the trial's
own rules (``evaluate.judge_move``), beside baselines a forecaster could have known that morning, with intervals
that respect how the moves hang together.

- **A move** is one factor, one horizon (3 days, 1 week), from one morning's origin, as ``eval_scores`` keeps it.
- **A track** gives some moves an expected move in the factor's unit. The agents' track is the replay's own scores
  (a morning's drafts merged as live); any other track is one forecast per move, judged as a single draft.
- **Fair baselines**, knowable at the origin's close: *momentum* (the move over the same horizon just before) and
  *the trailing 60-day majority* (the direction the horizon's moves mostly took in the 60 days before). The
  *hindsight* bar (always the commoner direction of the moves scored) stays beside them: it is not a forecaster.
- **Amount**: a forecast is big when it is at least a material move (``material_sigma`` × the horizon's scale).
- **Week blocks**: the factors of a morning move together and 1-week windows overlap, so the intervals and p-values
  resample whole weeks of origins, never single moves."""

from __future__ import annotations

import json
import random
import sqlite3
import statistics
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from trial import evaluate, shadow

HORIZONS = ("3d", "1w")
SCORED = ("correct", "incorrect", "missed", "quiet")
TRAILING_DAYS = 60
Key = Tuple[str, str, str]  # (morning, horizon, factor)


def _back(day: str, n: int) -> str:
    return (date.fromisoformat(day) - timedelta(days=n)).isoformat()


# -- the moves ---------------------------------------------------------------------------------------------------


def moves(state: Path) -> List[Dict[str, Any]]:
    """A replay's moves at 3 days and 1 week as scored: the agents' track, with the morning, horizon and factor."""
    con = sqlite3.connect(f"file:{state}?mode=ro", uri=True)
    q = "select day, horizon, factor, verdict, data from eval_scores where horizon in (?, ?) order by day, horizon, factor"
    out = [
        {**json.loads(d), "day": day, "horizon": h, "factor": f, "verdict": v}
        for day, h, f, v, d in con.execute(q, HORIZONS)
    ]
    con.close()
    return out


def key(r: Dict[str, Any]) -> Key:
    return (r["day"], r["horizon"], r["factor"])


def judge(
    track: Dict[Key, float], universe: List[Dict[str, Any]], series: Dict[str, Any], today: Optional[str] = None
) -> List[Dict[str, Any]]:
    """A track's verdicts on the universe's moves, by ``judge_move``: each forecast one draft made at 08:30 on the
    morning (after the origin's close, as live); a move it does not forecast is one it did not call."""
    today = today or date.today().isoformat()
    m, cfg = shadow.model(), evaluate.settings()
    out = []
    for r in universe:
        k = key(r)
        drafts = []
        if k in track:
            at = datetime.fromisoformat(r["day"]).replace(hour=8, minute=30).timestamp()
            drafts = [{"view_id": "lab", "created": at, "expected": track[k], "origin": r["origin"]}]
        got = evaluate.judge_move(r["day"], r["horizon"], m.factor(r["factor"]), drafts, True, series, today, cfg,
                                  m.horizons[r["horizon"]])
        out.append({**got, "day": r["day"], "horizon": r["horizon"], "factor": r["factor"]})
    return out


# -- the baselines -----------------------------------------------------------------------------------------------


def momentum(r: Dict[str, Any], series: Dict[str, Any]) -> Optional[float]:
    """The factor's move over the horizon just before the origin."""
    s = series.get(r["factor"])
    return s.move(_back(r["origin"], shadow.HORIZON_DAYS[r["horizon"]]), r["origin"]) if s else None


def majority(r: Dict[str, Any], series: Dict[str, Any], days: int = TRAILING_DAYS) -> Optional[float]:
    """The share of the horizon's moves that went up in the ``days`` before the origin (every move ended by then),
    as an expected move: (2 × share − 1) × the horizon's scale — up all the time is a material move up."""
    s = series.get(r["factor"])
    if not s:
        return None
    n = shadow.HORIZON_DAYS[r["horizon"]]
    xs = [s.move(_back(d, n), d) for d in (_back(r["origin"], i) for i in range(days))]
    xs = [x for x in xs if x]
    if not xs:
        return None
    return (2 * sum(x > 0 for x in xs) / len(xs) - 1) * r["scale"]


def baseline(fn: Callable, universe: List[Dict[str, Any]], series: Dict[str, Any]) -> Dict[Key, float]:
    out = {}
    for r in universe:
        x = fn(r, series)
        if x is not None:
            out[key(r)] = x
    return out


# -- the measures ------------------------------------------------------------------------------------------------


def _calls(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [r for r in rows if r["verdict"] in ("correct", "incorrect") and r.get("realised")]


def _hit(sign: Optional[float], x: float) -> Optional[bool]:
    return None if not sign else (sign > 0) == (x > 0)


def same_calls(rows: List[Dict[str, Any]], other: Dict[Key, float]) -> Dict[str, Any]:
    """Another forecaster's direction on the very moves the track called (where it has one)."""
    hits = [_hit(other.get(key(r)), r["realised"]) for r in _calls(rows)]
    hits = [h for h in hits if h is not None]
    return {"value": evaluate._share(sum(hits), len(hits)), "hits": sum(hits), "n": len(hits)}


def spearman(a: List[float], b: List[float]) -> Optional[float]:
    if len(a) < 3:
        return None
    rank = lambda xs: {i: k for k, i in enumerate(sorted(range(len(xs)), key=lambda i: xs[i]))}  # noqa: E731
    ra, rb = rank(a), rank(b)
    try:
        return round(statistics.correlation([ra[i] for i in range(len(a))], [rb[i] for i in range(len(b))]), 3)
    except statistics.StatisticsError:
        return None


def measures(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The gate's measures over judged rows: direction when the track calls, recall of the big moves, the amount
    (big moves forecast big, big forecasts that were big, both the right way) and the information coefficient."""
    done = [r for r in rows if r["verdict"] in SCORED and r.get("realised") is not None]
    big = [r for r in done if r["material"]]
    said = [r for r in done if r.get("expected") is not None and abs(r["expected"]) >= r["material_sigma"] * r["scale"]]
    right = lambda r: r["realised"] * r["expected"] > 0  # noqa: E731
    both = [r for r in said if r["material"] and right(r)]
    with_x = [r for r in done if r.get("expected") is not None]
    x = evaluate.rates(rows)
    return {
        "call_direction": {k: x["call_direction"][k] for k in ("value", "hits", "n")},
        "hindsight": x["call_direction"]["naive"],
        "recall": x["recall"],
        "precision": x["precision"],
        "amount_recall": {"value": evaluate._share(len(both), len(big)), "hits": len(both), "n": len(big)},
        "amount_precision": {"value": evaluate._share(len(both), len(said)), "hits": len(both), "n": len(said)},
        "ic": spearman([r["expected"] / r["scale"] for r in with_x], [r["realised"] / r["scale"] for r in with_x]),
        "moves": len(done),
    }


# -- week blocks -------------------------------------------------------------------------------------------------


def week(r: Dict[str, Any]) -> Tuple[int, int]:
    y, w, _ = date.fromisoformat(r["origin"]).isocalendar()
    return y, w


def bootstrap(
    rows: List[Dict[str, Any]], stat: Callable[[List[Dict[str, Any]]], Optional[float]], n: int = 2000, seed: int = 7
) -> List[float]:
    """``stat`` over ``n`` resamples of whole weeks of origins (with replacement)."""
    blocks: Dict[Tuple[int, int], List[Dict[str, Any]]] = {}
    for r in rows:
        blocks.setdefault(week(r), []).append(r)
    keys, rng, out = sorted(blocks), random.Random(seed), []
    for _ in range(n):
        got = stat([r for k in rng.choices(keys, k=len(keys)) for r in blocks[k]])
        if got is not None:
            out.append(got)
    return out


def interval(xs: List[float], level: float = 0.95) -> Tuple[Optional[float], Optional[float]]:
    if not xs:
        return None, None
    s = sorted(xs)
    lo, hi = s[int((1 - level) / 2 * len(s))], s[min(len(s) - 1, int((1 + level) / 2 * len(s)))]
    return round(lo, 3), round(hi, 3)


def accuracy(rows: List[Dict[str, Any]], other: Optional[Dict[Key, float]] = None) -> Optional[float]:
    """Direction on the track's calls (``other`` given: that forecaster's on the same calls)."""
    c = _calls(rows)
    hits = [(r["claim"] == "up") == (r["realised"] > 0) for r in c] if other is None else [
        h for h in (_hit(other.get(key(r)), r["realised"]) for r in c) if h is not None]
    return sum(hits) / len(hits) if hits else None


def edge(rows: List[Dict[str, Any]], other: Dict[Key, float]) -> Optional[float]:
    """The track's direction on its calls less the other forecaster's on the same calls."""
    a, b = accuracy(rows), accuracy(rows, other)
    return None if a is None or b is None else a - b


def report(rows: List[Dict[str, Any]], fair: Dict[str, Dict[Key, float]], n: int = 2000) -> Dict[str, Any]:
    """A track's measures, its call direction's week-block interval, and against each fair baseline on the same
    calls: that baseline's direction and the chance (week-block, one-sided) the track is no better."""
    out = measures(rows)
    out["interval"] = interval(bootstrap(rows, accuracy, n))
    out["fair"] = {}
    for name, other in fair.items():
        diffs = bootstrap(rows, lambda rs, o=other: edge(rs, o), n)
        out["fair"][name] = {
            **same_calls(rows, other),
            "p": round(sum(d <= 0 for d in diffs) / len(diffs), 4) if diffs else None,
        }
    return out

"""The morning desk (FORECAST_DESK_PLAN step 5): one call after the morning's events that reads every draft of the
morning beside the market, the statistical odds, past headlines like today's and the record, and forecasts each
factor at 3 days and 1 week: a direction, how sure, and how far (in σ, the horizon's typical move).

- **The drafts** are the per-event agents' (the BRD flow, unchanged): each event's title, why, summary and its
  shadow forecasts in σ. They forecast one event's effect; the desk forecasts the market.
- **The record** is the desk's own past calls and the per-event agents', only moves over by the origin's close.
- **A forecast** becomes one draft of the desk's track: expected = direction × size × the horizon's scale; "flat"
  or a size under the claim share is no call (``judge_move`` decides as for any draft)."""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional, Tuple

from trial import kb as kbase
from trial import shadow

HORIZONS = ("3d", "1w")
MAX_TOKENS = 6000

SYSTEM = """You are the morning desk of a Vietnamese private bank's investment office. Every morning, before the
market opens, you forecast how each market factor moves from yesterday's close over the next 3 days and the next
week. You are scored on every factor and horizon:

- A call is a direction (up or down) with a size of at least 0.25 sigma. It is right when the market moves at
  least 1 sigma that way (a "big" move). A call on a move that stays under 1 sigma counts against you, and a big
  move you did not call is missed. Sigma is the factor's typical move at that horizon; about a fifth of moves are
  big.
- So call when the evidence points to a move of about a sigma or more, say "flat" otherwise, and give the size you
  really expect: a call of 1.2 sigma that is right is worth more than a hedged 0.3.

What you read (DATA):
- "events": this morning's news events with the per-event analysts' forecasts in sigma ("drafts"). They forecast
  the effect of one event alone and, as their record shows, their sizes run small; treat them as evidence about the
  news, not as the market forecast.
- "market": per factor, its own recent moves in sigma of each window (m3d, m1w, m1m, m3m), its volatility against
  its year (vol, log ratio), where it sits in its 1-year range (-1 low .. +1 high), the share of up moves of each
  horizon in the last 60 days ("up60", -1..+1), and a statistical model's chance of up ("p_up") and of a big move
  ("p_big") fitted on 2020-2026H1. Big moves cluster: when vol is high and the recent moves are large, big moves
  are more likely.
- "analogs": per factor and horizon, what followed past headlines most like today's (mean move in sigma, share up,
  number of days), when available.
- "record": how your past calls and the analysts' went, on moves already over.

Answer with JSON only:
{"calls": [{"factor": "<id>", "horizon": "3d"|"1w", "direction": "up"|"down"|"flat", "p": <0.5-1, how sure of the
direction>, "size": <expected absolute move in sigma>, "why": "<one short sentence in Vietnamese>"}]}
with one entry for every factor in "market" and both horizons."""


def sigma(fid: str, horizon: str, m: Any) -> float:
    return m.factor(fid).vol_month * math.sqrt(m.horizons[horizon])


def drafts(day: str, events: List[Dict[str, Any]], shadows: List[Dict[str, Any]], views: Dict[str, Any],
           m: Any) -> List[Dict[str, Any]]:
    """The morning's events with each draft's forecasts in σ (a factor under 0.1σ left out)."""
    by_view: Dict[str, Dict[str, Dict[str, float]]] = {}
    for f in shadows:
        if f["horizon"] in HORIZONS:
            z = f["expected"] / sigma(f["factor"], f["horizon"], m)
            if abs(z) >= 0.1:
                by_view.setdefault(f["view_id"], {}).setdefault(f["horizon"], {})[f["factor"]] = round(z, 2)
    out = []
    for e in events:
        v = views.get(e.get("view_id") or "")
        if not v:
            continue
        out.append({
            "title": e["title"],
            "why": e.get("why"),
            "summary": (v.get("current") or {}).get("summary", "")[:700],
            "drafts": by_view.get(v["id"], {}),
        })
    return out


def record(origin: str, past: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Per horizon, how ``past`` judged rows went (only moves over by the origin): calls right, calls on small
    moves, big moves missed; by factor family."""
    out: Dict[str, Any] = {}
    for h in HORIZONS:
        rows = [r for r in past if r["horizon"] == h and r.get("due") and r["due"] <= origin
                and r["verdict"] in ("correct", "incorrect", "missed", "quiet")]
        if not rows:
            continue
        calls = [r for r in rows if r["verdict"] in ("correct", "incorrect")]
        big = [r for r in rows if r.get("material")]
        out[h] = {
            "calls": len(calls),
            "direction_right": sum((r["claim"] == "up") == (r["realised"] > 0) for r in calls),
            "big_and_right": sum(r["verdict"] == "correct" for r in calls),
            "big_moves": len(big),
            "big_missed": sum(r["verdict"] == "missed" for r in rows),
            "median_size_ratio": _median([abs(r["expected"]) / abs(r["realised"]) for r in rows
                                          if r.get("expected") and r.get("realised")]),
        }
    return out


def _median(xs: List[float]) -> Optional[float]:
    xs = sorted(xs)
    return round(xs[len(xs) // 2], 2) if xs else None


def packet(day: str, origin: str, events: List[Dict[str, Any]], series: Dict[str, Any], m: Any,
           odds: Any = None, base: Optional[kbase.Base] = None, history: Optional[Dict[str, List]] = None
           ) -> Dict[str, Any]:
    """What the desk reads this morning; every number from before the origin's close."""
    market = {}
    for fid in sorted(series):
        f = m.factor(fid)
        row: Dict[str, Any] = {"name": f.name, "unit": f.unit,
                               "sigma": {h: round(sigma(fid, h, m), 3) for h in HORIZONS}}
        if odds is not None:
            for h in HORIZONS:
                got = odds.of(fid, origin, h)
                if got:
                    row.setdefault("features", got["features"])
                    row[h] = {"p_up": got["p_up"], "p_big": got["p_big"]}
        market[fid] = row
    out: Dict[str, Any] = {"day": day, "origin": origin, "events": events, "market": market}
    if base is not None:
        texts = [f"{e['title']} {e.get('why') or ''}" for e in events]
        out["analogs"] = {h: kbase.analogs(base, texts, origin, h, series, m) for h in HORIZONS} if texts else {}
    if history:
        out["record"] = {who: record(origin, rows) for who, rows in history.items()}
    return out


def parse(got: Dict[str, Any], origin: str, day: str, series: Dict[str, Any], m: Any
          ) -> Dict[Tuple[str, str, str], float]:
    """The desk's calls as a track: expected = ±size × the horizon's σ; flat is 0."""
    out = {}
    for c in got.get("calls") or []:
        fid, h = c.get("factor"), c.get("horizon")
        if fid not in series or h not in HORIZONS:
            continue
        sign = {"up": 1, "down": -1}.get(c.get("direction"), 0)
        try:
            size = max(0.0, float(c.get("size") or 0))
        except (TypeError, ValueError):
            size = 0.0
        out[(day, h, fid)] = sign * size * sigma(fid, h, m)
    return out


async def call(p: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    from views import agents

    text, meta = await agents.call_model("cio", SYSTEM, agents.wrap(p), MAX_TOKENS)
    return agents._json(text), meta


def dumps(track: Dict[Tuple[str, str, str], float]) -> str:
    return json.dumps({"|".join(k): round(v, 6) for k, v in sorted(track.items())})

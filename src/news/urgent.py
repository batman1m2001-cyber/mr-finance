"""Urgent events (BRD-KPI-01 “tin khẩn ≤ 30 phút”; BRD_REMAINING_PLAN G6, G-D6). The BRD does not say what makes
news urgent; until the bank does, this is our reading, labelled “Đề xuất” wherever it shows:

- **The CIO decides.** An event is urgent when the CIO flags it, with a reason (``events.store.set_urgent``),
  audited. Only flagged events are measured against the 30 minutes.
- **The product proposes**, when the event is grouped (data/news_config.json ``urgent``):
  - an SBV decision on the policy rate or the FX band: the news names the SBV and the decision's words;
  - a market move past ``sigma`` (3) standard deviations of the factor's daily moves over the last ``window_days``
    (250) market days, on the latest market day up to the event, for each factor the event touches.

A daily move is in the factor's unit (control: market/factors.py): % for a level, basis points for a yield,
percentage points for a gap, the day's value for net foreign buying.
"""

from __future__ import annotations

import math
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from news import rules

STALE_DAYS = 4  # the latest market day must be this close to the event, or there is nothing to compare


def _config() -> Dict[str, Any]:
    from news.ops import config

    return config()["urgent"]


def daily_moves(unit: str, points: List[tuple]) -> List[tuple]:
    """``[(day, move)]`` from ``[(day, value)]``, in the factor's unit."""
    if unit == "sd":
        return list(points)
    out = []
    for (_, v0), (d1, v1) in zip(points, points[1:]):
        if unit == "pct":
            if v0:
                out.append((d1, (v1 / v0 - 1) * 100))
        elif unit == "bp":
            out.append((d1, (v1 - v0) * 100))
        else:  # pp
            out.append((d1, v1 - v0))
    return out


def big_move(factor: str, at: float, cfg: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """The factor's move on the latest market day up to ``at``, when it is past ``sigma`` deviations."""
    from market import factors

    cfg = cfg or _config()
    back = factors.backing().get(factor)
    unit = next((f["unit"] for f in factors._model_factors() if f["id"] == factor), None)
    if back is None or unit is None:
        return None
    day = datetime.fromtimestamp(at).date().isoformat()
    mv = [m for m in daily_moves(unit, factors.values(back["series"])) if m[0] <= day]
    window = int(cfg["window_days"])
    if len(mv) < window + 1:
        return None
    last_day, last = mv[-1]
    if date.fromisoformat(day) - date.fromisoformat(last_day) > timedelta(days=STALE_DAYS):
        return None
    hist = [x for _, x in mv[-window - 1 : -1]]
    mean = sum(hist) / len(hist)
    sd = math.sqrt(sum((x - mean) ** 2 for x in hist) / (len(hist) - 1))
    if sd <= 0:
        return None
    z = (last - mean) / sd
    if abs(z) <= float(cfg["sigma"]):
        return None
    return {
        "factor": factor,
        "series": back["series"],
        "day": last_day,
        "move": round(last, 4),
        "unit": unit,
        "z": round(z, 2),
        "sd": round(sd, 4),
    }


def proposals(factor_ids: List[str], items: List[Dict[str, Any]], at: Optional[float] = None) -> List[Dict[str, Any]]:
    """Why the product proposes an event as urgent (empty: it does not)."""
    cfg = _config()
    at = time.time() if at is None else at
    text = " ".join(f"{i.get('title', '')} {i.get('summary', '')}" for i in items).lower()
    out: List[Dict[str, Any]] = []
    if rules._any(cfg["actor_words"], text):
        for d in cfg["decisions"]:
            if rules._any(d["words"], text):
                out.append({"kind": "decision", "id": d["id"], "reason": d["label"]})
    for f in factor_ids:
        try:
            m = big_move(f, at, cfg)
        except Exception:  # noqa: BLE001 — a series that cannot be read proposes nothing; the CIO still decides
            m = None
        if m:
            unit = {"pct": "%", "bp": " điểm cơ bản", "pp": " điểm %", "sd": ""}[m["unit"]]
            move = f"{m['move']:+.2f}".replace(".", ",") + unit
            out.append(
                {
                    "kind": "move",
                    **m,
                    "reason": f"{f} biến động {move} ngày {m['day']}, {abs(m['z']):.1f} lần độ lệch chuẩn".replace(
                        ".", ",", 1
                    ),
                }
            )
    return out

"""The model scored on history, walking forward (FEAT-18; BRD-RULE-MEAS-01/02, KPI-03/04).

At every origin the model is estimated from the months that had ended by then (``market.estimate``, 55-month
window, at least 24 months), and only what it knew is used to forecast what came after:

- **Band coverage (MEAS-01, KPI-04).** With no scenario the engine's band for a factor at a horizon is centred on
  0 with sd = σ × √months × realisation (``engine.scenario.factor_bands`` for one branch with no shock). Is the
  realised move inside P10–P90? Accept 70–90 %; fewer than 24 observations is not yet a conclusion.
- **Direction (MEAS-02, KPI-03).** The engine's second step out of sample: given what the *other* factors did over
  the period, the conditional expectation Σfc Σcc⁻¹ Δc of this one (BRD §9.1 step 2). Did it have the right sign?
  This is the engine's direction when the CIO calls the core shocks right; the views' own calls are scored in
  ``measure.forecasts``.

Origins: every 7 days for 1 week; every month end for 3 and 12 months — so those periods overlap and their
observations are not independent (said on the page).
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from control import config
from engine import FactorModel, linalg
from market import estimate
from measure import realised

HORIZON_DAYS = {"1w": 7, "3m": 91, "12m": 365}
MIN_OBS = 24
DIRECTION_TARGET = 0.70  # BRD-KPI-03
Z80 = estimate.Z80
ACCEPT = estimate.ACCEPT


def verdict(n: int, share: Optional[float]) -> str:
    if share is None or n == 0:
        return "chưa có"
    if n < MIN_OBS:
        return "chưa đủ 24 quan sát"
    return "đạt" if ACCEPT[0] <= share <= ACCEPT[1] else ("dải hẹp" if share < ACCEPT[0] else "dải rộng")


def _month_end(month: str) -> str:
    y, m = map(int, month.split("-"))
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return (nxt - timedelta(days=1)).isoformat()


def _months(first: str, last: str) -> List[str]:
    out, (y, m) = [], map(int, first.split("-"))
    while f"{y:04d}-{m:02d}" <= last:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)
    return out


def _known_month(day: str) -> str:
    """The last month that had ended by the end of ``day``."""
    d = date.fromisoformat(day) + timedelta(days=1)
    return estimate._month_back(f"{d.year:04d}-{d.month:02d}", 1)


def origins(horizon: str, first_month: str, last_day: str) -> List[str]:
    days = HORIZON_DAYS[horizon]
    last_origin = realised.add_days(last_day, -days)
    if horizon == "1w":
        out, d = [], _month_end(first_month)
        while d <= last_origin:
            out.append(d)
            d = realised.add_days(d, 7)
        return out
    return [e for e in (_month_end(m) for m in _months(first_month, last_day[:7])) if e <= last_origin]


def run(
    hist: Optional[Dict[str, Dict[str, Any]]] = None,
    data: Optional[Dict[str, realised.Series]] = None,
    base: Optional[Dict[str, Any]] = None,
    start: Optional[str] = None,
) -> Dict[str, Any]:
    """Walk forward over every origin from ``start`` (default: the first month any factor can be estimated)."""
    base = base or config.data("factor_model")
    hist = estimate.history() if hist is None else hist
    data = realised.series() if data is None else data
    names = {f["id"]: f["name"] for f in base["factors"]}
    units = {f["id"]: f["unit"] for f in base["factors"]}
    if not hist or not data:
        return {"horizons": {}, "from": None, "to": None, "kpi03": None}
    first = min(min(h["moves"]) for h in hist.values())
    start = start or estimate._month_back(first, -(estimate.MIN_MONTHS - 1))
    last_day = max(s.last for s in data.values())
    models: Dict[str, Any] = {}

    def model_at(month: str):
        if month not in models:
            m = estimate.estimate(base, end=month, hist=hist)["model"]
            fm = FactorModel.from_dict(m)
            models[month] = (fm, {f["id"] for f in m["factors"] if not f.get("assumed")})
        return models[month]

    out: Dict[str, Any] = {}
    for h, days in HORIZON_DAYS.items():
        rows = {fid: {"inside": 0, "n": 0, "hits": 0, "dn": 0, "abs": 0.0} for fid in data if fid in names}
        os_ = origins(h, start, last_day)
        for o in os_:
            fm, est = model_at(_known_month(o))
            end = realised.add_days(o, days)
            moves = {fid: data[fid].move(o, end) for fid in rows if fid in est}
            moves = {k: v for k, v in moves.items() if v is not None}
            ids = [k for k in fm.ids if k in moves]
            if not ids:
                continue
            cov = fm.cov["normal"]
            idx = {k: fm.index(k) for k in ids}
            for fid in ids:
                f = fm.factor(fid)
                sd = math.sqrt(cov[idx[fid]][idx[fid]] * fm.horizons[h]) * f.realisation[h]
                r, x = rows[fid], moves[fid]
                r["n"] += 1
                r["abs"] += abs(x)
                r["inside"] += abs(x) <= Z80 * sd
                others = [k for k in ids if k != fid]
                if not others or x == 0:
                    continue
                cc = linalg.sub(cov, [idx[k] for k in others], [idx[k] for k in others])
                fc = [cov[idx[fid]][idx[k]] for k in others]
                w = linalg.solve_spd(cc, [[v] for v in fc])
                mu = sum(w[i][0] * moves[k] for i, k in enumerate(others))
                if mu == 0:
                    continue
                r["dn"] += 1
                r["hits"] += (mu > 0) == (x > 0)
        factors = []
        for fid, r in rows.items():
            if not r["n"]:
                continue
            cov_share = r["inside"] / r["n"]
            hit = r["hits"] / r["dn"] if r["dn"] else None
            factors.append(
                {
                    "id": fid,
                    "name": names[fid],
                    "unit": units[fid],
                    "n": r["n"],
                    "coverage": round(cov_share, 3),
                    "verdict": verdict(r["n"], cov_share),
                    "direction_n": r["dn"],
                    "direction_hit": round(hit, 3) if hit is not None else None,
                    "mean_abs_move": round(r["abs"] / r["n"], 3),
                }
            )
        total = sum(f["n"] for f in factors)
        pooled = sum(f["coverage"] * f["n"] for f in factors) / total if total else None
        out[h] = {
            "days": days,
            "origins": len(os_),
            "step": "7 ngày" if h == "1w" else "cuối mỗi tháng",
            "overlapping": h != "1w",
            "factors": factors,
            "pooled_coverage": round(pooled, 3) if pooled is not None else None,
            "pooled_verdict": verdict(total, pooled),
        }
    vn = {h: next((f for f in out[h]["factors"] if f["id"] == "VNINDEX"), None) for h in out}
    kpi03 = {
        h: {"n": f["direction_n"], "hit": f["direction_hit"], "met": _met(f["direction_n"], f["direction_hit"])}
        for h, f in vn.items()
        if f
    }
    return {"from": _month_end(start), "to": last_day, "horizons": out, "kpi03": kpi03, "target": DIRECTION_TARGET}


def _met(n: int, hit: Optional[float]) -> Optional[bool]:
    if hit is None or n < MIN_OBS:
        return None
    return hit >= DIRECTION_TARGET


_CACHE: Dict[Any, Dict[str, Any]] = {}


def cached() -> Dict[str, Any]:
    """``run()`` for the history and the model in force, computed again only when either changes."""
    from market import store

    key = (store.stamp(), config.active_hash("factor_model"))
    if key not in _CACHE:
        _CACHE.clear()
        _CACHE[key] = run()
    return _CACHE[key]

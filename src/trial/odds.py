"""The market snapshot and the statistical odds (FORECAST_DESK_PLAN step 3): per factor at an origin's close, what
its own series and the world's markets did before it, and logistic models of the chance the next 3 days or week
goes up, and goes far (a material move).

- **Only before the origin**: every feature is a move or level ended on or before the origin's close.
- **In σ**: a move over a window is divided by the factor's typical move over that window (``vol_month`` × √months),
  so the factors share one model; each factor keeps its own intercept (gold's drift is not the dollar's).
- **Trained on 2020 → 2026-06** (moves due by the last day of training), dev and test after it: the models never
  saw a move they are measured on."""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from trial import shadow

WINDOWS = {"m3d": 3, "m1w": 7, "m1m": 30, "m3m": 91}
WORLD = ("GLOBAL_EQ", "DXY", "US10Y", "BRENT")
OVERNIGHT = ("GLOBAL_EQ", "BTC")  # their last day closes after Vietnam's and before the morning
DAYS_PER_MONTH = 30.4375


def _back(day: str, n: int) -> str:
    return (date.fromisoformat(day) - timedelta(days=n)).isoformat()


def _sigma(f: Any, days: int) -> float:
    return f.vol_month * math.sqrt(days / DAYS_PER_MONTH)


def _moves(s: Any, origin: str, n: int, back: int) -> List[float]:
    """The factor's ``n``-day moves ended on each of the ``back`` days up to the origin."""
    xs = [s.move(_back(d, n), d) for d in (_back(origin, i) for i in range(back))]
    return [x for x in xs if x is not None]


def snapshot(fid: str, origin: str, horizon: str, series: Dict[str, Any], m: Any) -> Optional[Dict[str, float]]:
    """The factor's features at the origin's close (None without its own month before)."""
    s, f = series.get(fid), m.factor(fid)
    if s is None or s.move(_back(origin, 30), origin) is None:
        return None
    out: Dict[str, float] = {}
    for k, n in WINDOWS.items():
        x = s.move(_back(origin, n), origin)
        out[k] = 0.0 if x is None else x / _sigma(f, n)
    n = shadow.HORIZON_DAYS[horizon]
    trail = _moves(s, origin, n, 60)
    out["up60"] = 2 * sum(x > 0 for x in trail) / len(trail) - 1 if trail else 0.0
    weekly_now, weekly_year = _moves(s, origin, 7, 30)[::7], _moves(s, origin, 7, 365)[::7]
    if len(weekly_now) > 2 and len(weekly_year) > 10:
        sd = lambda xs: float(np.std(xs)) or 1e-9  # noqa: E731
        out["vol"] = math.log(sd(weekly_now) / sd(weekly_year))
    else:
        out["vol"] = 0.0
    year = [s.level(d) for d in (_back(origin, i) for i in range(0, 365, 3))]
    year = [v for v in year if v is not None]
    now = s.level(origin)
    if s.unit != "sd" and now is not None and year:
        hi, lo = max(year), min(year)
        out["range"] = (now - lo) / (hi - lo) * 2 - 1 if hi > lo else 0.0
    else:
        out["range"] = 0.0
    for w in WORLD:
        ws = series.get(w)
        x = ws.move(_back(origin, 7), origin) if ws else None
        out[f"w_{w}"] = 0.0 if x is None else x / _sigma(m.factor(w), 7)
    for w in OVERNIGHT:
        ws = series.get(w)
        x = ws.move(_back(origin, 1), origin) if ws else None
        out[f"d_{w}"] = 0.0 if x is None else x / _sigma(m.factor(w), 1)
    x = s.move(_back(origin, 1), origin)
    out["m1d"] = 0.0 if x is None else x / _sigma(f, 1)
    return out


FEATURES = ("m1d",) + tuple(WINDOWS) + ("up60", "vol", "range") + tuple(f"w_{w}" for w in WORLD) + tuple(
    f"d_{w}" for w in OVERNIGHT)
# how far it goes reads the size of what came before, not its sign: big moves come in clusters
SIZES = tuple(WINDOWS) + ("vol", "range", "w_GLOBAL_EQ")


def row(feats: Dict[str, float], fid: str, factors: List[str], kind: str = "up") -> np.ndarray:
    """The up model is the factor's own (each market leads or follows others its own way): its features and an
    intercept. The big model is shared: the sizes before it and each factor's intercept."""
    clip = lambda v: max(-4.0, min(4.0, v))  # noqa: E731
    if kind == "up":
        return np.array([clip(feats[k]) for k in FEATURES] + [1.0])
    x = [feats["vol"] if k == "vol" else abs(clip(feats[k])) for k in SIZES]
    return np.array(x + [1.0 if fid == g else 0.0 for g in factors])


def fit(X: np.ndarray, y: np.ndarray, l2: float = 1.0, steps: int = 30) -> np.ndarray:
    """L2 logistic regression by Newton's method (the factor intercepts are the last columns)."""
    w = np.zeros(X.shape[1])
    reg = l2 * np.eye(X.shape[1])
    for _ in range(steps):
        p = 1 / (1 + np.exp(-X @ w))
        g = X.T @ (p - y) + reg @ w
        H = (X * (p * (1 - p))[:, None]).T @ X + reg
        step = np.linalg.solve(H, g)
        w -= step
        if np.abs(step).max() < 1e-8:
            break
    return w


def prob(w: np.ndarray, x: np.ndarray) -> float:
    return float(1 / (1 + math.exp(-float(x @ w))))


def training(series: Dict[str, Any], m: Any, horizon: str, first: str, last: str, every: int = 2
             ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """Features (the up model's, the big model's) and outcomes (up, material) of every factor's move from origins
    ``first``..``last`` whose due day is no later than ``last`` (one origin every ``every`` days), and whose move each is."""
    factors = sorted(series)
    n = shadow.HORIZON_DAYS[horizon]
    months = m.horizons[horizon]
    X, Xb, up, big, who = [], [], [], [], []
    d = first
    end = _back(last, n)
    while d <= end:
        for fid in factors:
            s = series[fid]
            y = s.move(d, shadow.realised.add_days(d, n))
            if y is None or y == 0:
                continue
            feats = snapshot(fid, d, horizon, series, m)
            if feats is None:
                continue
            X.append(row(feats, fid, factors))
            Xb.append(row(feats, fid, factors, "big"))
            who.append(fid)
            up.append(1.0 if y > 0 else 0.0)
            big.append(1.0 if abs(y) >= m.factor(fid).vol_month * math.sqrt(months) else 0.0)
        d = shadow.realised.add_days(d, every)
    return np.array(X), np.array(Xb), np.array(up), np.array(big), who


class Odds:
    """The two models per horizon, trained once."""

    def __init__(self, series: Dict[str, Any], first: str = "2020-04-01", last: str = "2026-06-30", l2: float = 5.0,
                 l2_up: float = 50.0):
        self.series, self.m = series, shadow.model()
        self.factors = sorted(series)
        self.w: Dict[str, Dict[str, Any]] = {}
        self.base: Dict[str, float] = {}
        for h in ("3d", "1w"):
            X, Xb, up, big, who = training(series, self.m, h, first, last)
            mine = {f: np.array([w == f for w in who]) for f in self.factors}
            self.w[h] = {"up": {f: fit(X[k], up[k], l2_up) for f, k in mine.items() if k.sum() > 50},
                         "big": fit(Xb, big, l2)}
            self.base[h] = float(big.mean())

    def of(self, fid: str, origin: str, horizon: str) -> Optional[Dict[str, Any]]:
        feats = snapshot(fid, origin, horizon, self.series, self.m)
        if feats is None:
            return None
        up, big = row(feats, fid, self.factors), row(feats, fid, self.factors, "big")
        w_up = self.w[horizon]["up"].get(fid)
        return {"p_up": round(prob(w_up, up), 3) if w_up is not None else 0.5,
                "p_big": round(prob(self.w[horizon]["big"], big), 3),
                "features": {k: round(v, 2) for k, v in feats.items()}}

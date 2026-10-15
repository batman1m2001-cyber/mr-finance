"""The factors' moves made from the stored series (F1 ``factor_series``; read by the estimation in F2).

Each factor of the model is either backed by a stored or computed series, or stays assumed (“Giả định”: no free
source; data/market_sources.json ``assumed``). A move is month-end to month-end, in the factor's unit:

- ``pct``: the percentage change of the level;
- ``bp``: the change of a yield in %, ×100;
- ``pp``: the change of a gap in percentage points (SJC_GAP);
- ``sd``: the month's net foreign buying, standardised over the months stored (FOREIGN_FLOW).

Computed series: the DXY by ICE's published formula from six currencies, and the SJC gap (SJC's price against
world gold in VND per lượng: XAU × USD/VND × 37.5 / 31.1035), each day the inputs exist (the latest known value of
an input carries over a day it is missing).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from market import fetch, store

LUONG_PER_OZ = 37.5 / 31.1035  # one lượng is 37.5 g; one troy ounce 31.1035 g
DXY = {"EURUSD": -0.576, "USDJPY": 0.136, "GBPUSD": -0.119, "USDCAD": 0.091, "USDSEK": 0.042, "USDCHF": 0.036}
DXY_K = 50.14348112

Point = Tuple[str, float]


def _carry(series: Dict[str, List[Point]], days: List[str]) -> Dict[str, Dict[str, float]]:
    """Each input's value on each day: its own, else the latest before it."""
    out: Dict[str, Dict[str, float]] = {}
    for sid, pts in series.items():
        it, last, vals = 0, None, {}
        for d in days:
            while it < len(pts) and pts[it][0] <= d:
                last = pts[it][1]
                it += 1
            if last is not None:
                vals[d] = last
        out[sid] = vals
    return out


def dxy(inputs: Optional[Dict[str, List[Point]]] = None) -> List[Point]:
    inputs = inputs or {k: store.points(k) for k in DXY}
    if not all(inputs.get(k) for k in DXY):
        return []
    days = sorted({d for k in DXY for d, _ in inputs[k]})
    vals = _carry(inputs, days)
    out = []
    for d in days:
        if all(d in vals[k] for k in DXY):
            out.append((d, DXY_K * math.prod(vals[k][d] ** w for k, w in DXY.items())))
    return out


def sjc_gap(inputs: Optional[Dict[str, List[Point]]] = None) -> List[Point]:
    """SJC's premium over world gold, in % (SJC's own days only)."""
    inputs = inputs or {k: store.points(k) for k in ("SJC", "XAUUSD", "USDVND")}
    if not all(inputs.get(k) for k in ("SJC", "XAUUSD", "USDVND")):
        return []
    days = [d for d, _ in inputs["SJC"]]
    vals = _carry({k: inputs[k] for k in ("XAUUSD", "USDVND")}, days)
    out = []
    for d, sjc in inputs["SJC"]:
        if d in vals["XAUUSD"] and d in vals["USDVND"]:
            world = vals["XAUUSD"][d] * vals["USDVND"][d] * LUONG_PER_OZ
            out.append((d, (sjc / world - 1) * 100))
    return out


COMPUTED = {"DXY": dxy, "SJC_GAP": sjc_gap}


def values(series_id: str) -> List[Point]:
    """A stored series, or a computed one."""
    return COMPUTED[series_id]() if series_id in COMPUTED else store.points(series_id)


def month_ends(points: List[Point]) -> List[Tuple[str, float]]:
    out: Dict[str, float] = {}
    for d, v in points:
        out[d[:7]] = v  # sorted by day: the month's last point wins
    return sorted(out.items())


def month_sums(points: List[Point]) -> List[Tuple[str, float]]:
    out: Dict[str, float] = {}
    for d, v in points:
        out[d[:7]] = out.get(d[:7], 0.0) + v
    return sorted(out.items())


def moves(unit: str, points: List[Point]) -> List[Dict[str, Any]]:
    """Month-to-month moves in the factor's unit (see the module's docstring)."""
    if unit == "sd":
        sums = month_sums(points)
        if len(sums) < 3:
            return []
        xs = [v for _, v in sums]
        mean = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / (len(xs) - 1)) or 1.0
        return [{"month": m, "move": (v - mean) / sd} for m, v in sums]
    ends = month_ends(points)
    out = []
    for (m0, v0), (m1, v1) in zip(ends, ends[1:]):
        if unit == "pct":
            mv = (v1 / v0 - 1) * 100 if v0 else None
        elif unit == "bp":
            mv = (v1 - v0) * 100
        else:  # pp
            mv = v1 - v0
        if mv is not None:
            out.append({"month": m1, "move": mv})
    return out


def _model_factors() -> List[Dict[str, Any]]:
    from control import config

    return config.data("factor_model")["factors"]


def backing() -> Dict[str, Dict[str, Any]]:
    """Factor id → the series behind it and how to label it."""
    cat = fetch.catalogue()
    out: Dict[str, Dict[str, Any]] = {}
    for s in cat["series"]:
        if s.get("factor"):
            out[s["factor"]] = {"series": s["id"], "name": s["name"], "note": s.get("note"), "computed": False}
    for sid, c in (cat.get("computed") or {}).items():
        out[c["factor"]] = {"series": sid, "name": c["name"], "note": None, "computed": True}
    return out


def factor_series(with_moves: bool = False) -> List[Dict[str, Any]]:
    """Every factor of the model in force: its series, provenance label, months of moves and the latest move."""
    back = backing()
    assumed = set(fetch.catalogue().get("assumed") or [])
    cov = store.coverage()
    out = []
    for f in _model_factors():
        b = back.get(f["id"])
        row: Dict[str, Any] = {"id": f["id"], "name": f["name"], "unit": f["unit"]}
        if b is None or f["id"] in assumed:
            row.update(provenance="Giả định", series=None, months=0)
            out.append(row)
            continue
        pts = values(b["series"])
        mv = moves(f["unit"], pts)
        last_src = (cov.get(b["series"]) or {}).get("source")
        label = "Tính từ dữ liệu thị trường" if b["computed"] else f"Dữ liệu thị trường ({last_src or 'chưa có'})"
        if b["note"]:
            label += " · thay thế"
        row.update(
            provenance=label if pts else "Giả định (chưa có dữ liệu)",
            series=b["series"],
            note=b["note"],
            first=pts[0][0] if pts else None,
            last=pts[-1][0] if pts else None,
            months=len(mv),
            last_move=mv[-1] if mv else None,
        )
        if with_moves:
            row["moves"] = mv
        out.append(row)
    return out

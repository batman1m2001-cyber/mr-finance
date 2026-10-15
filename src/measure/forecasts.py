"""Every approved view's forecast for every factor and horizon, kept and scored when the horizon has passed
(FEAT-18; BR-15, BRD-RULE-MEAS-01/02, KPI-03/04).

- **Recorded at approval.** The view's branches through the engine (``engine.factor_bands``, the model in force):
  for each of the 15 factors and each horizon the expected move and P10 / P50 / P90 in the factor's unit, from the
  day it was approved (``origin``) to ``origin`` + 7 / 91 / 365 days (``due``). Views approved before this existed
  are recorded by the daily job with the model in force then, and say so (``late``).
- **Scored by the daily job** once the factor's series reaches the due day: the realised move (``measure.realised``),
  inside P10–P90 or not, and — when the forecast had a direction — whether the move went the same way. A factor
  with no series (assumed) is never scored; one whose data has not come 30 days after the due day is closed as
  “không có dữ liệu”.

A view withdrawn or superseded later stays scored: the record is of what was approved.
"""

from __future__ import annotations

import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from control import db
from engine import default_model, factor_bands
from measure import backtest, realised
from views import schema
from views import store as vstore

HORIZON_DAYS = backtest.HORIZON_DAYS
GIVE_UP_DAYS = 30
SCORED = ("APPROVED", "SUPERSEDED", "WITHDRAWN")


def _approved_at(view: Dict[str, Any]) -> Optional[float]:
    return next((h["at"] for h in reversed(view.get("history", [])) if h["status"] == "APPROVED"), None)


def record(view: Dict[str, Any], late: bool = False) -> int:
    """Keep the view's forecasts (once: a view already recorded is left as it is)."""
    at = _approved_at(view)
    if at is None:
        return 0
    with db.tx() as con:
        if con.execute("select 1 from forecasts where view_id = ? limit 1", (view["id"],)).fetchone():
            return 0
    cur = view["current"]
    model = default_model()
    bands = factor_bands(schema.to_engine(cur["scenarios"]["branches"], cur["scenarios"]["priced_in"]), model)
    origin = datetime.fromtimestamp(at).date().isoformat()
    now = time.time()
    rows = []
    for h, by_factor in bands.items():
        due = realised.add_days(origin, HORIZON_DAYS[h])
        for fid, b in by_factor.items():
            data = {
                **b,
                "unit": model.factor(fid).unit,
                "event_id": view["event_id"],
                "model": model.version,
                "late": late,
            }
            rows.append((f"{view['id']}:{h}:{fid}", view["id"], fid, h, origin, due, now, None, db.dumps(data)))
    with db.tx() as con:
        con.executemany("insert or ignore into forecasts values (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    return len(rows)


def record_missing() -> List[str]:
    """Record the views approved before forecasts were kept (the daily job; idempotent)."""
    with db.tx() as con:
        have = {r[0] for r in con.execute("select distinct view_id from forecasts")}
        ids = [r[0] for r in con.execute("select id from views where status in (?, ?, ?)", SCORED)]
    done = []
    for vid in ids:
        if vid not in have and record(vstore.get(vid), late=True):
            done.append(vid)
    return done


def score(today: Optional[str] = None, data: Optional[Dict[str, realised.Series]] = None) -> Dict[str, int]:
    """Score every forecast whose due day has passed and whose factor's data has reached it."""
    today = today or date.today().isoformat()
    with db.tx() as con:
        due = [db.load(r) for r in con.execute("select * from forecasts where scored is null and due < ?", (today,))]
    if not due:
        return {"scored": 0, "no_data": 0, "waiting": 0}
    data = realised.series() if data is None else data
    out = {"scored": 0, "no_data": 0, "waiting": 0}
    now = time.time()
    updates = []
    for f in due:
        s = data.get(f["factor"])
        x = s.move(f["origin"], f["due"]) if s and s.last and s.last >= f["due"] else None
        if x is None:
            late = (date.fromisoformat(today) - date.fromisoformat(f["due"])).days > GIVE_UP_DAYS
            if s is None or late:
                f.update(result="no_data")
                out["no_data"] += 1
            else:
                out["waiting"] += 1
                continue
        else:
            exp = f["expected"]
            f.update(
                result="scored",
                realised=round(x, 6),
                inside=f["p10"] <= x <= f["p90"],
                direction_hit=None if exp == 0 or x == 0 else (exp > 0) == (x > 0),
            )
            out["scored"] += 1
        data_only = {
            k: v
            for k, v in f.items()
            if k not in ("id", "view_id", "factor", "horizon", "origin", "due", "created", "scored")
        }
        updates.append((now, db.dumps(data_only), f["id"]))
    with db.tx() as con:
        con.executemany("update forecasts set scored = ?, data = ? where id = ?", updates)
    return out


def all_rows() -> List[Dict[str, Any]]:
    with db.tx() as con:
        return [db.load(r) for r in con.execute("select * from forecasts order by origin, view_id, horizon, factor")]


def summary(rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Per horizon and factor: forecasts kept, scored, inside the band, direction calls and hits."""
    rows = all_rows() if rows is None else rows
    names = {f.id: f.name for f in default_model().factors}
    out: Dict[str, Any] = {}
    for h in HORIZON_DAYS:
        mine = [r for r in rows if r["horizon"] == h]
        factors = []
        for fid in names:
            fr = [r for r in mine if r["factor"] == fid]
            if not fr:
                continue
            sc = [r for r in fr if r.get("result") == "scored"]
            calls = [r for r in sc if r.get("direction_hit") is not None]
            inside = sum(1 for r in sc if r["inside"])
            hits = sum(1 for r in calls if r["direction_hit"])
            factors.append(
                {
                    "id": fid,
                    "name": names[fid],
                    "kept": len(fr),
                    "pending": sum(1 for r in fr if r.get("scored") is None),
                    "no_data": sum(1 for r in fr if r.get("result") == "no_data"),
                    "n": len(sc),
                    "coverage": round(inside / len(sc), 3) if sc else None,
                    "verdict": backtest.verdict(len(sc), inside / len(sc) if sc else None),
                    "direction_n": len(calls),
                    "direction_hit": round(hits / len(calls), 3) if calls else None,
                }
            )
        pending = [r for r in mine if r.get("scored") is None]
        out[h] = {
            "factors": factors,
            "next_due": min((r["due"] for r in pending), default=None),
            "views": len({r["view_id"] for r in mine}),
        }
    vn = {h: next((f for f in out[h]["factors"] if f["id"] == "VNINDEX"), None) for h in out}
    kpi03 = {
        h: {
            "n": f["direction_n"],
            "hit": f["direction_hit"],
            "met": backtest._met(f["direction_n"], f["direction_hit"]),
        }
        for h, f in vn.items()
        if f
    }
    return {"horizons": out, "kpi03": kpi03, "views": len({r["view_id"] for r in rows})}


def for_view(view_id: str) -> List[Dict[str, Any]]:
    with db.tx() as con:
        return [
            db.load(r)
            for r in con.execute("select * from forecasts where view_id = ? order by horizon, factor", (view_id,))
        ]

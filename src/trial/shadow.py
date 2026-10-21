"""The trial's shadow forecasts (B1.2, B1.3): a draft's forecast for every factor at 3 days, 1 week and 3 months,
kept when the challenger has finished with it, never approved, scored like FEAT-18's (``forecasts.judge``).

- **Origin** is the close before the draft was made: the agents run in the morning, before the market opens, so the
  first move scored is one they could not see.
- **3 days** is not a horizon of the factor model: it is the 1-week realisation over a tenth of a month, labelled
  uncalibrated in the report (1 week and 3 months are the model's own).
- **Each scenario's own path** is kept beside the mixture's, so the report can say which scenario the market took
  and whether it was the one the agents rated most likely.
- **A buy or sell reading** for the assets a client holds (VN-Index, gold, Bitcoin, the dollar): the mixture's
  expected move against a quarter of a typical move at that horizon — above it "mua", below minus it "bán", else
  "giữ". A reading for the report, never advice."""

from __future__ import annotations

import dataclasses
import math
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from control import db
from engine import default_model, factor_bands
from engine.model import FactorModel
from measure import forecasts, realised
from views import schema

HORIZON_DAYS = {"3d": 3, "1w": 7, "3m": 91}
UNCALIBRATED = ("3d",)
CALLS = {"VNINDEX": "Cổ phiếu (VN-Index)", "GOLD": "Vàng", "BTC": "Bitcoin", "USDVND": "Đô la (USD/VND)"}
CALL_SHARE = 0.25  # of a typical move at the horizon: a smaller expected move is "giữ"
RECORDED = ("PENDING_APPROVAL", "APPROVED", "REWORK_REQUESTED", "REJECTED", "WITHDRAWN", "SUPERSEDED")


def model() -> FactorModel:
    """The model in force with the trial's horizons: 3 days added (the 1-week realisation), 12 months left out."""
    m = default_model()
    factors = [dataclasses.replace(f, realisation={**f.realisation, "3d": f.realisation["1w"]}) for f in m.factors]
    horizons = {"3d": 0.1, "1w": m.horizons["1w"], "3m": m.horizons["3m"]}
    return dataclasses.replace(m, horizons=horizons, factors=factors)


def origin_of(at: float) -> str:
    """The close before ``at``: the day before it (``Series.level`` takes the last trading day on or before)."""
    return (datetime.fromtimestamp(at).date() - timedelta(days=1)).isoformat()


def call(expected: float, factor: Any, months: float) -> str:
    edge = CALL_SHARE * factor.vol_month * math.sqrt(months)
    return "mua" if expected > edge else "bán" if expected < -edge else "giữ"


def record(view: Dict[str, Any], trial: Dict[str, Any]) -> int:
    """Keep the draft's shadow forecasts (once per view)."""
    with db.tx() as con:
        if con.execute("select 1 from shadow_forecasts where view_id = ? limit 1", (view["id"],)).fetchone():
            return 0
    cur = view["current"]
    m = model()
    branches = schema.to_engine(cur["scenarios"]["branches"], cur["scenarios"]["priced_in"])
    bands = factor_bands(branches, m)
    paths = {b["id"]: factor_bands([{**b, "probability": 1.0}], m) for b in branches}
    origin = trial.get("origin") or origin_of(view["created"])  # the replay (B1.5) gives the day it plays
    now = time.time()
    rows = []
    for h, by_factor in bands.items():
        due = realised.add_days(origin, HORIZON_DAYS[h])
        for fid, band in by_factor.items():
            f = m.factor(fid)
            data = {
                **band,
                "unit": f.unit,
                "event_id": view["event_id"],
                "segment": trial.get("segment"),
                "region": trial.get("region"),
                "model": m.version,
                "branches": [
                    {"id": b["id"], "p": round(b["probability"], 4), "expected": paths[b["id"]][h][fid]["expected"]}
                    for b in branches
                ],
                "call": call(band["expected"], f, m.horizons[h]) if fid in CALLS else None,
            }
            rows.append((f"{view['id']}:{h}:{fid}", view["id"], fid, h, origin, due, now, None, db.dumps(data)))
    with db.tx() as con:
        con.executemany("insert or ignore into shadow_forecasts values (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    return len(rows)


def score(today: Optional[str] = None, data: Optional[Dict[str, realised.Series]] = None) -> Dict[str, int]:
    """Every shadow forecast whose due day has passed, against the stored market data."""
    today = today or date.today().isoformat()
    with db.tx() as con:
        q = "select * from shadow_forecasts where scored is null and due < ?"
        due = [db.load(r) for r in con.execute(q, (today,))]
    out = {"scored": 0, "no_data": 0, "waiting": 0}
    if not due:
        return out
    data = realised.series() if data is None else data
    now = time.time()
    updates = []
    for f in due:
        got = forecasts.judge(f, data, today)
        out[got] += 1
        if got == "waiting":
            continue
        keep = ("id", "view_id", "factor", "horizon", "origin", "due", "created", "scored")
        updates.append((now, db.dumps({k: v for k, v in f.items() if k not in keep}), f["id"]))
    with db.tx() as con:
        con.executemany("update shadow_forecasts set scored = ?, data = ? where id = ?", updates)
    return out


def rows() -> List[Dict[str, Any]]:
    with db.tx() as con:
        q = "select * from shadow_forecasts order by origin, view_id, horizon, factor"
        return [db.load(r) for r in con.execute(q)]

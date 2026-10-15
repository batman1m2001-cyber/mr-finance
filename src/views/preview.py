"""FR-305: before approving, what each branch does to the market — every factor's move, as the
engine propagates it, realised at 1 week / 3 months / 12 months. Market level only: no client."""

from __future__ import annotations

from typing import Any, Dict, List

from engine import default_model, propagate
from engine.scenario import Branch
from views import schema


def preview(current: Dict[str, Any]) -> List[Dict[str, Any]]:
    model = default_model()
    sc = current["scenarios"]
    out = []
    for b in schema.to_engine(sc["branches"], sc["priced_in"]):
        p = propagate(Branch.from_dict({**b, "probability": 1.0}), model)
        moves = []
        for f, m in zip(model.factors, p.moves):
            if abs(m) < 1e-9:
                continue
            moves.append(
                {
                    "factor": f.id,
                    "name": f.name,
                    "unit": f.unit,
                    "core": model.index(f.id) in p.core,
                    "move": round(m, 4),
                    "realised": {h: round(m * f.realisation[h], 4) for h in model.horizons},
                }
            )
        moves.sort(key=lambda x: (not x["core"], -abs(x["move"]) / model.factor(x["factor"]).vol_month))
        out.append(
            {"id": b["id"], "name": b["name"], "probability": b["probability"], "regime": b["regime"], "moves": moves}
        )
    return out

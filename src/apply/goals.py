"""Goal impact of a run (BRD FR-404): each goal's funding before and after, with Đạt / Theo dõi / Thiếu.

Our reading (Q-11, for the CIO to confirm): a family's dated goals draw, in date order, on its financial
assets (cash, deposits, funds, bonds, stocks, gold, crypto). Before = their values in the snapshot;
after = the same plus the run's 3-month expected change of each of those holdings. The level is the
goals-planning rule (``scenarios._sim.goal``): the monthly saving that would close the gap by the goal's
date, over the family's monthly surplus — ≤ 0.6 Đạt, ≤ 1 Theo dõi, above (or no surplus) Thiếu; no gap
is Đạt. Pure: the same snapshot gives the same numbers.

BR-08 (VND summed by goal): the pool's own impact — the engine run on the pooled holdings, so every horizon with
its expected value and P5 / P10 / P50 / P90 — is shared out by each goal's slice of the pool before the run
(``have ÷ pool``); what no goal takes is ``unallocated``. Scaling by a fixed share keeps the percentiles exact,
and the goals plus the unallocated part add up to the pool's change.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from scenarios import _sim

POOL = ("cash", "deposit", "fund", "bond", "stock", "gold", "crypto")
LEVEL = {_sim.ON_TRACK: "Đạt", _sim.AT_RISK: "Theo dõi", _sim.OFF_TRACK: "Thiếu"}


def _months(as_of: date, due: date) -> int:
    return max(1, (due.year - as_of.year) * 12 + due.month - as_of.month)


def _fund(goals: List[Dict[str, Any]], pool: float, surplus: float, as_of: date) -> List[Dict[str, Any]]:
    out, left = [], pool
    for g in goals:
        need = float(g["amount"])
        have = max(0.0, min(need, left))
        left -= have
        gap = need - have
        monthly = gap / _months(as_of, date.fromisoformat(g["date"])) if gap > 0 else 0.0
        status = _sim.goal(need, have, monthly, surplus, by=g["date"], actions=[])["status"]
        out.append({"have": have, "ratio": have / need if need else 1.0, "status": status, "level": LEVEL[status]})
    return out


STATS = ("expected", "p5", "p10", "p50", "p90")


def goal_impacts(
    family: Dict[str, Any], by_holding: Dict[str, float], as_of: str, pool_bands: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """The family's goals before and after the run's 3-month expected change (empty without goals); with
    ``pool_bands`` (the engine's horizons for the pooled holdings) each goal's VND impact by horizon (BR-08)."""
    goals = sorted((g for g in family.get("goals") or [] if g.get("amount")), key=lambda g: (g["date"], g["goal_id"]))
    pooled = [h for h in family["holdings"] if h["kind"] == "asset" and h["class"] in POOL]
    before = sum(h["value"] for h in pooled)
    change = sum(by_holding.get(h["key"], 0.0) for h in pooled)
    day, surplus = date.fromisoformat(as_of), float(family.get("surplus_monthly") or 0.0)
    pre, post = _fund(goals, before, surplus, day), _fund(goals, before + change, surplus, day)
    out = {
        "pool": {"before": before, "after": before + change, "change": change},
        "goals": [
            {
                **{k: g[k] for k in ("goal_id", "label", "date", "amount")},
                "before": a,
                "after": b,
                "changed": a["level"] != b["level"],
            }
            for g, a, b in zip(goals, pre, post)
        ],
    }
    if pool_bands is not None and goals:
        share = [a["have"] / before if before > 0 else 0.0 for a in pre]
        bands = {h: {x: float(v[x]) for x in STATS} for h, v in pool_bands.items()}
        for g, s in zip(out["goals"], share):
            g["share"] = s
            g["impact"] = {h: {x: round(s * v[x]) for x in STATS} for h, v in bands.items()}
        rest = max(0.0, 1.0 - sum(share))
        out["pool"]["bands"] = {h: {x: round(v[x]) for x in STATS} for h, v in bands.items()}
        out["unallocated"] = {
            "share": rest,
            "impact": {h: {x: round(rest * v[x]) for x in STATS} for h, v in bands.items()},
        }
    return out

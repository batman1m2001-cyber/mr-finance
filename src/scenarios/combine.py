"""Several stress tests at once, without double counting (UNIFIED_FLOWS_PLAN F4, OWN-GW-39/40).

- **Assets compound per holding:** ``after = value × Π(1 + shockᵢ)``. Two shocks never apply twice to the same base,
  so two −50 % falls make −75 %, not −100 %.
- **Attribution by Shapley value:** each scenario is credited with its average marginal change over the orders in
  which the scenarios could be applied. The parts add up to the combined change exactly, whatever the signs.
- **Costs by key** (``floating_interest``, ``fx_spending``): the same key from two scenarios counts once, the larger.
  It is credited to the scenario that set it.
- **Net worth after** = assets after − debt − one year of the costs: the standalone stress rule (``_sim._stress``),
  so combining one scenario gives exactly its standalone result.
- **Liquidity, income and expenses after:** the liquid holdings after their shocks; spending plus the costs ÷ 12;
  income changed by the person's what-if.
- **Goals:** each followed goal recomputed on the shocked picture, the same way the goals page computes it.

Nothing here touches the client's records: the result is a what-if, never added to net worth."""

from __future__ import annotations

from itertools import combinations
from math import factorial, prod
from typing import Any, Dict, List, Optional

from scenarios import _sim
from wealth.money import vnd

GROUP = {"cash": "deposit"}  # the overview's class nodes (overview.ops.GROUP): cash sits with deposits
NOTE = "Giả định — không phải giao dịch, không cộng vào tài sản ròng."
MAX = 6  # Shapley over 2⁶ subsets at most


def _shapley(shocks: List[float], value: float) -> List[float]:
    """Each scenario's share of ``value × (Π(1 + sᵢ) − 1)``: its average marginal change over all orders."""
    n = len(shocks)
    out = []
    for i in range(n):
        others = [j for j in range(n) if j != i]
        total = 0.0
        for k in range(n):
            w = factorial(k) * factorial(n - k - 1) / factorial(n)
            for sub in combinations(others, k):
                total += w * shocks[i] * prod(1 + shocks[j] for j in sub)
        out.append(value * total)
    return out


def _liquid(holdings: List[Dict[str, Any]]) -> float:
    return sum(
        h["value"]
        for h in holdings
        if h["kind"] == "asset" and (h["class"] in ("cash", "deposit") or (h["class"] == "fund" and h["liquid"]))
    )


def _goals(p: _sim.Pic, followed: Optional[List[str]]) -> Dict[str, Dict[str, Any]]:
    out = {}
    for sid, meta in _sim.SCENARIOS.items():
        if meta["kind"] != "life" or not meta.get("stage"):
            continue
        if followed is not None and sid not in followed:
            continue
        if followed is None and p.profile["persona_hint"] not in meta["personas"]:
            continue
        g = meta["run"](p, {})["goal"]
        out[sid] = {k: g[k] for k in ("need", "have", "gap", "monthly", "surplus", "status")} | {"title": meta["title"]}
    return out


def combine(
    p: _sim.Pic,
    ids: List[str],
    params: Optional[Dict[str, Dict[str, Any]]] = None,
    followed: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """The active stress tests ``ids`` (in the order given) on the picture ``p``."""
    params = params or {}
    ids = list(dict.fromkeys(ids))  # the same scenario twice is once
    for sid in ids:
        if sid not in _sim.SHOCKS:
            raise ValueError(f"no stress scenario {sid!r}; one of {sorted(_sim.SHOCKS)}")
    if len(ids) > MAX:
        raise ValueError(f"at most {MAX} scenarios together")
    specs = [(sid, _sim.SHOCKS[sid](p, params.get(sid) or {})) for sid in ids]

    per = {
        sid: {
            "id": sid,
            "title": _sim.SCENARIOS[sid]["title"],
            "assumptions": sk.assumptions,
            "by_class": {},
            "change": 0.0,
            "costs": {},
        }
        for sid, sk in specs
    }
    by_class: Dict[str, float] = {}
    shocked: List[Dict[str, Any]] = []
    for h in p.holdings:
        if h["kind"] != "asset" or not specs:
            shocked.append(h)
            continue
        s = [sk.shock(h) for _, sk in specs]
        if not any(s):
            shocked.append(h)
            continue
        after = h["value"] * prod(1 + x for x in s)
        change = after - h["value"]
        c = GROUP.get(h["class"], h["class"])
        by_class[c] = by_class.get(c, 0.0) + change
        for (sid, _), part in zip(specs, _shapley(s, h["value"])):
            if part:
                per[sid]["by_class"][c] = per[sid]["by_class"].get(c, 0.0) + part
                per[sid]["change"] += part
        shocked.append({**h, "value": after})

    costs: Dict[str, Dict[str, Any]] = {}
    for sid, sk in specs:  # one cost per key: the larger, credited to the scenario that set it
        for key, cst in sk.costs.items():
            cur = costs.get(key)
            if cur is None:
                costs[key] = {**cst, "key": key, "by": sid, "also": []}
            elif cst["amount"] > cur["amount"]:
                costs[key] = {**cst, "key": key, "by": sid, "also": cur["also"] + [cur["by"]]}
            else:
                cur["also"].append(sid)
    for cst in costs.values():
        per[cst["by"]]["costs"][cst["key"]] = cst["amount"]
    yearly = sum(c["amount"] for c in costs.values())
    income = next((sk.income for _, sk in specs if sk.income), 0.0)

    before_assets = p.value()
    after_assets = sum(h["value"] for h in shocked if h["kind"] == "asset")
    debt = p.debt
    spending, income_m = p.spending, p.profile.get("income_monthly") or 0
    spending_after = spending + yearly / 12
    income_after = income_m * (1 + income)
    liquid_after = _liquid(shocked)
    profile_after = {**p.profile, "income_monthly": income_after, "spending_monthly": spending_after}
    p_after = _sim.Pic(holdings=shocked, profile=profile_after, market=p.market)
    goals_before, goals_after = _goals(p, followed), _goals(p_after, followed)

    nw_before = before_assets - debt
    nw_after = after_assets - debt - yearly
    warnings = [
        f"{c['label']}: {len(c['also']) + 1} kịch bản cùng giả định — tính một lần ({vnd(c['amount'])}/năm)"
        for c in costs.values()
        if c["also"]
    ]
    return {
        "active": ids,
        "scenarios": [per[sid] for sid in ids],
        "by_class": by_class,
        "costs": list(costs.values()),
        "before": {
            "net_worth": nw_before,
            "assets": before_assets,
            "liabilities": debt,
            "liquid": p.liquid,
            "liquid_months": p.liquid / spending,
            "income": income_m,
            "spending": spending,
            "surplus": income_m - spending,
        },
        "after": {
            "net_worth": nw_after,
            "assets": after_assets,
            "liabilities": debt,
            "liquid": liquid_after,
            "liquid_months": liquid_after / spending_after,
            "income": income_after,
            "spending": spending_after,
            "surplus": income_after - spending_after,
        },
        "change": nw_after - nw_before,
        "goals": [
            {"id": gid, "title": g["title"], "before": g, "after": goals_after[gid]} for gid, g in goals_before.items()
        ],
        "warnings": warnings,
        "note": NOTE,
    }

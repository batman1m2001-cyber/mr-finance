"""Several stress tests together (UNIFIED_FLOWS_PLAN F4/F5, OWN-GW-37/39/40): one engine, no double counting —
shocks compound per holding, each scenario's part is its Shapley value and the parts add up, a cost two scenarios
both assume counts once, the person's what-if moves income and with it the goals, and nothing touches the records."""

import asyncio
import copy

import pytest
from operonx import Operon

from scenarios import _sim
from scenarios.combine import combine
from scenarios.graph import combine_flow, scenario_flow
from wealth import fixtures
from wealth.money import TR, TY

COMBINE = Operon(
    combine_flow, params={"client_id": None, "scenarios": None, "params": None, "scope": None, "goals": None}
)
SINGLE = Operon(scenario_flow, params={"client_id": None, "scenario": None, "params": None, "scope": None})
STRESS = [sid for sid, m in _sim.SCENARIOS.items() if m["kind"] == "stress" and sid != "custom"]


def run(engine, **inputs):
    out = asyncio.run(engine.run(inputs=inputs))
    assert "$errors" not in out, out.get("$errors")
    return out["result"]


def both(cid, ids, params=None, scope="personal"):
    return run(COMBINE, client_id=cid, scenarios=ids, params=params or {}, scope=scope, goals=None)


def pic(holdings, income=60 * TR, spending=40 * TR):
    profile = {"income_monthly": income, "spending_monthly": spending, "drawdown_limit": 0.2, "persona_hint": "-",
               "events": []}  # fmt: skip
    return _sim.Pic(holdings=holdings, profile=profile, market={"as_of": "2026-10-09"})


def asset(key, cls, value, **detail):
    return {"key": key, "name": key, "kind": "asset", "class": cls, "value": value, "liquid": False, "detail": detail}


def test_one_scenario_combined_is_its_standalone_result():
    for cid in fixtures.client_ids():
        for sid in STRESS:
            alone, together = run(SINGLE, client_id=cid, scenario=sid, params={}, scope="personal"), both(cid, [sid])
            assert together["after"]["net_worth"] == pytest.approx(alone["after"]["net_worth"], abs=1), (cid, sid)
            assert together["by_class"].keys() == {_c(c) for c in alone["by_class"]} or not alone["by_class"]
            assert sum(together["by_class"].values()) == pytest.approx(sum(alone["by_class"].values()), abs=1)
            assert {c["key"]: c["amount"] for c in together["costs"]} == {
                k: c["amount"] for k, c in alone["costs"].items()
            }


def _c(cls):
    return {"cash": "deposit"}.get(cls, cls)


def test_shocks_compound_on_a_holding_never_add():
    p = pic([asset("VNM", "stock", 100 * TR, beta=1)])
    r = combine(p, ["vni_30", "custom"], {"custom": {"stock": -0.5}})
    assert r["by_class"]["stock"] == pytest.approx(-65 * TR)  # 100 × 0.7 × 0.5 = 35, not 100 − 30 − 50 = 20
    parts = {s["id"]: s["change"] for s in r["scenarios"]}
    assert sum(parts.values()) == pytest.approx(-65 * TR)  # the parts add up to the whole, exactly
    assert parts["vni_30"] == pytest.approx(-30 * TR + 7.5 * TR)  # its own −30 + half the interaction (+15)
    assert parts["custom"] == pytest.approx(-50 * TR + 7.5 * TR)


def test_the_parts_add_up_whatever_the_signs():
    p = pic([asset("SJC", "gold", 200 * TR), asset("VNM", "stock", 100 * TR, beta=1.2)])
    r = combine(p, ["usd_up", "custom", "vni_30"], {"custom": {"gold": -0.5, "stock": 0.2}})
    for cls in ("gold", "stock"):
        assert sum(s["by_class"].get(cls, 0) for s in r["scenarios"]) == pytest.approx(r["by_class"][cls])
    assert r["by_class"]["gold"] == pytest.approx(200 * TR * (1.015 * 0.5 - 1))
    assert r["change"] == pytest.approx(r["after"]["net_worth"] - r["before"]["net_worth"])


def test_a_cost_two_scenarios_assume_counts_once():
    loan = {"key": "L", "name": "Vay", "kind": "liability", "class": "loan", "value": 2 * TY, "liquid": False,
            "detail": {"rate_type": "floating"}}  # fmt: skip
    p = pic([asset("D", "deposit", 1 * TY), loan])
    r = combine(p, ["rates_up", "custom"], {"custom": {"rate": 0.03}})
    assert [(c["key"], c["amount"], c["by"], c["also"]) for c in r["costs"]] == [
        ("floating_interest", 2 * TY * 0.03, "custom", ["rates_up"])
    ]
    assert r["warnings"] and "tính một lần" in r["warnings"][0]
    assert r["after"]["net_worth"] == pytest.approx(1 * TY - 2 * TY - 2 * TY * 0.03)  # one year of it, once
    assert r["after"]["spending"] == pytest.approx(40 * TR + 2 * TY * 0.03 / 12)
    smaller = combine(p, ["custom", "rates_up"], {"custom": {"rate": 0.01}})  # the larger wins, whatever the order
    assert [(c["amount"], c["by"]) for c in smaller["costs"]] == [(2 * TY * 0.02, "rates_up")]


def test_the_persons_what_if_moves_income_and_the_goals_follow():
    r = both("C01", ["custom"], {"custom": {"income": -0.5}})
    assert r["after"]["income"] == pytest.approx(r["before"]["income"] * 0.5)
    assert r["after"]["surplus"] < r["before"]["surplus"]
    assert r["change"] == 0  # income is not wealth: net worth does not move
    assert r["goals"] and all(g["after"]["surplus"] == pytest.approx(r["after"]["surplus"]) for g in r["goals"])
    assert [s["assumptions"] for s in r["scenarios"]] == [["Thu nhập hằng tháng -50%"]]


def test_the_records_are_never_touched():
    p = pic([asset("VNM", "stock", 100 * TR, beta=1), asset("D", "deposit", 50 * TR)])
    before = copy.deepcopy(p.holdings)
    combine(p, ["vni_30", "custom"], {"custom": {"stock": -0.4, "income": 0.1}})
    assert p.holdings == before and p.net_worth == 150 * TR


def test_the_same_scenario_twice_is_once_and_bad_input_is_refused():
    p = pic([asset("VNM", "stock", 100 * TR, beta=1)])
    assert combine(p, ["vni_30", "vni_30"], {})["by_class"]["stock"] == pytest.approx(-30 * TR)
    with pytest.raises(ValueError):
        combine(p, ["tuition"], {})  # a life event is a goal, not a shock
    with pytest.raises(ValueError):
        combine(p, ["custom"], {"custom": {"stock": -0.9}})
    with pytest.raises(ValueError):
        combine(p, ["custom"], {"custom": {"rate": "a lot"}})
    assert combine(p, [], {})["change"] == 0  # nothing active: nothing changes


def test_liquidity_after_counts_the_shocked_liquid_funds():
    fund = {**asset("F", "fund", 100 * TR, fund_type="equity"), "liquid": True}
    r = combine(pic([fund, asset("D", "deposit", 100 * TR)]), ["vni_30"], {})
    assert r["before"]["liquid"] == 200 * TR and r["after"]["liquid"] == pytest.approx(172 * TR)

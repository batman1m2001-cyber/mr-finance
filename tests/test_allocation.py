"""ASSET_ALLOCATION_BRD: the three buckets on the worked example K-7F3A (§11), every number the BRD states; the model's
tilt kept in range; the checks; the flows on the sample families; the RM's send to the review queue."""

import asyncio
import json

import pytest
from operonx import Operon

from allocation import _engine, _model, ops
from allocation.graph import (
    allocation_example_flow,
    allocation_flow,
    allocation_send_flow,
    allocation_tilt_flow,
    allocation_tilts_flow,
)
from views.schema import forbidden_words
from wealth import fixtures, store
from wealth.money import TY, TR

FLOW = Operon(allocation_flow, params={"client_id": None, "scope": None, "method": None, "assumptions": None, "role": None})
EXAMPLE = Operon(allocation_example_flow, params={"method": None, "assumptions": None, "role": None})
TILT = Operon(allocation_tilt_flow, params={"asset_class": None, "stance": None, "view_id": None, "by": None, "reason": None})
TILTS = Operon(allocation_tilts_flow, params={})
SEND = Operon(allocation_send_flow, params={"client_id": None, "by": None, "scope": None, "method": None, "assumptions": None})


def run(engine, **inputs):
    return asyncio.run(engine.run(inputs=inputs))


def ok(engine, **inputs):
    out = run(engine, **inputs)
    assert "$errors" not in out, out["$errors"]
    return out


def case():
    return json.loads(ops.EXAMPLE.read_text(encoding="utf-8"))


def near(x, ty, tol=0.05):
    return abs(x / TY - ty) <= tol


@pytest.fixture(scope="module")
def k7():
    return _engine.allocate(case(), "A")


def test_the_three_liquidity_targets_and_the_ladder_of_k7(k7):
    liq = k7["liquidity"]
    assert near(liq["target"], 19) and near(liq["have"], 8) and near(liq["short"], 11)
    assert near(liq["targets"]["B"], 8.6) and near(liq["targets"]["C"], 16.9)
    assert [round(r["amount"] / TY, 1) for r in liq["ladder"]] == [3.0, 5.0, 5.5, 5.5]
    assert k7["cashflow"]["trough"]["month"] == "2029-03" and near(k7["cashflow"]["trough"]["cum"], -7.1)
    assert round(k7["cashflow"]["rate_shock"]["monthly"]) == 5 * TR


def test_liquidity_is_filled_by_selling_the_overweight_class_not_by_waiting_or_borrowing(k7):
    f = k7["fill"]
    assert f["chosen"] == "sell" and f["sells"] == {"equity": pytest.approx(11 * TY)}
    why = {o["id"]: o for o in f["options"]}
    assert not why["wait"]["ok"] and "03/2027" in why["wait"]["why"]
    assert not why["borrow"]["ok"]


def test_legacy_floor_target_and_gap_of_k7(k7):
    g = k7["legacy"]
    assert near(g["floor"], 40.5) and near(g["target"], 60) and near(g["have"], 44) and near(g["have_low"], 36)
    assert near(g["gap"], 16) and near(g["gap_high"], 24)


def test_growth_after_the_fill_is_rebalanced_to_the_tilted_model(k7):
    re_ = k7["growth"]["rebalance"]
    assert near(re_["total"], 31)
    trade = {r["class"]: r["trade"] / TY for r in re_["rows"]}
    assert round(trade["equity"], 1) == -3.7 and round(trade["bond"], 1) == 2.9 and round(trade["gold"], 1) == -2.9
    assert round(trade["cash"], 1) == 3.7
    m = k7["model"]["classes"]
    assert m["equity"]["target"] == pytest.approx(0.43) and m["cash"]["target"] == pytest.approx(0.12)
    assert k7["growth"]["worst_after"]["share"] < k7["growth"]["worst_before"]["share"]


def test_retirement_needs_more_than_the_model_expects(k7):
    r = k7["retirement"]
    assert round(r["expected"], 3) == 0.083 and round(r["required"], 3) == 0.092
    assert near(r["short"], 13.4, 0.1) and round(r["extra_monthly"] / TR, 1) == 57.8
    assert r["delay"]["enough"] == 3 and r["delay"]["near"]["years"] == 2


def test_the_buckets_add_up_to_the_assets_and_net_worth(k7):
    rec = k7["reconcile"]
    assert rec["assets"] == 100 * TY and rec["debts"] == 6 * TY and rec["net_worth"] == 94 * TY
    assert rec["buckets"] == rec["assets"]


def test_every_action_of_a_simulated_profile_warns_and_none_is_a_recommendation(k7):
    acts = k7["actions"]
    assert len(acts) == 7 and [a["n"] for a in acts] == list(range(1, 8))
    assert all(a["check"] == {"status": "WARN", "reasons": ["Hồ sơ giả lập"]} for a in acts)
    assert not any(forbidden_words(f"{a['what']} {a['why']}") for a in acts)
    assert "NHNN tăng lãi suất điều hành" in acts[1]["why"]


def test_the_same_case_gives_the_same_answer():
    assert _engine.allocate(case(), "C") == _engine.allocate(case(), "C")


def test_a_buy_above_the_level_range_is_blocked_and_hidden_from_the_client():
    c = case()
    c["risk"] = {"level": 3, "name": "Cân bằng", "source": "test", "at": "2026-09-01"}
    c["excluded"] = ["bond"]
    a = _engine.allocate(c, "A")
    bond = next(x for x in a["actions"] if x.get("class") == "bond")
    assert bond["check"]["status"] == "BLOCK" and "loại trừ" in bond["check"]["reasons"][0]
    shown = ops._for("client", a)
    assert bond["n"] not in {x["n"] for x in shown["actions"]}


def test_an_old_risk_test_warns():
    c = case()
    c["risk"] = {"level": 3, "name": "Cân bằng", "source": "test", "at": "2025-06-01"}
    a = _engine.allocate(c, "A")
    assert any("quá 12 tháng" in r for x in a["actions"] for r in x["check"]["reasons"])


def test_tilts_move_two_points_cap_at_five_and_stay_in_range():
    up = {"asset_class": "equity", "stance": "overweight", "view": "v"}
    one = _model.tilted(3, [up])["classes"]
    assert one["equity"]["tilt"] == pytest.approx(0.02) and one["cash"]["tilt"] == pytest.approx(-0.02)
    many = _model.tilted(3, [up] * 4)["classes"]
    assert abs(many["equity"]["tilt"]) <= 0.05 + 1e-9
    for lv in range(1, 6):
        for t in (up, {"asset_class": "gold", "stance": "underweight"}, {"asset_class": "cash", "stance": "overweight"}):
            m = _model.tilted(lv, [t] * 3)["classes"]
            assert sum(v["target"] for v in m.values()) == pytest.approx(1.0)
            assert all(v["low"] - 1e-9 <= v["target"] <= v["high"] + 1e-9 for v in m.values())


def test_certain_income_counts_wages_pensions_and_rent_only():
    tx = [
        {"date": "2026-01-05", "amount": 100, "direction": "in", "category": "salary"},
        {"date": "2026-01-06", "amount": 50, "direction": "in", "category": "dividend"},
        {"date": "2026-02-03", "amount": 20, "direction": "in", "category": "rent"},
    ]
    assert ops.certain_income(tx, 1000) == pytest.approx(120 / 12)
    assert ops.certain_income(tx, 5) == 5
    assert ops.certain_income([], 1000) == 0.0


def test_a_client_with_no_risk_test_gets_the_nearest_level_simulated():
    r = ops.risk_of("C03", 0.30)
    assert r["source"] == "simulated" and r["level"] == 4
    store.put_result("C03", "risk", {"taken": "2026-10-01", "profile": {"level": 2, "name": "Thận trọng"}})
    assert ops.risk_of("C03", 0.30) == {"level": 2, "name": "Thận trọng", "source": "test", "at": "2026-10-01"}


@pytest.mark.parametrize("cid", ["C01", "C02", "C03", "C04", "C05"])
def test_the_flow_runs_for_every_sample_family_and_reconciles(cid):
    a = ok(FLOW, client_id=cid)["allocation"]
    assert a["reconcile"]["buckets"] <= a["reconcile"]["assets"]
    assert a["actions"] and all(a_["check"]["status"] in ("PASS", "WARN", "BLOCK") for a_ in a["actions"])
    assert not any(forbidden_words(f"{x['what']} {x['why']}") for x in a["actions"])


def test_the_example_flow_and_its_methods():
    for m in "ABC":
        a = ok(EXAMPLE, method=m)["allocation"]
        assert a["method"] == m and a["example"]["id"] == "K-7F3A"
    assert "$errors" in run(EXAMPLE, method="D")
    assert "$errors" in run(EXAMPLE, assumptions={"nope": 1})
    a = ok(EXAMPLE, assumptions={"horizon_years": 5, "legacy_wish": 0})["allocation"]
    assert a["assumptions"]["horizon_years"] == 5


def test_a_cio_tilts_from_an_approved_view_and_the_case_reads_it(monkeypatch):
    from views import store as views

    monkeypatch.setattr(views, "approved", lambda: [{"id": "V-1", "current": {"summary": "Lãi suất tăng"}}])
    assert "$errors" in run(TILT, asset_class="equity", stance="overweight", view_id="V-9", by="cio")
    assert "$errors" in run(TILT, asset_class="equity", stance="overweight", view_id="V-1", by="rm01")
    out = ok(TILT, asset_class="equity", stance="underweight", view_id="V-1", by="cio")
    assert [t["stance"] for t in out["tilts"]] == ["underweight"]
    assert out["model"][3]["classes"]["equity"]["target"] == pytest.approx(0.43)
    a = ok(FLOW, client_id="C01")["allocation"]
    assert a["model"]["classes"]["equity"]["views"] == ["Lãi suất tăng"]
    assert ok(TILT, asset_class="equity", stance="neutral", view_id="V-1", by="cio")["tilts"] == []


def test_the_cio_page_reads_the_tilts_in_force_and_the_model_they_give(monkeypatch):
    from views import store as views

    monkeypatch.setattr(views, "approved", lambda: [{"id": "V-1", "current": {"summary": "Lãi suất tăng"}}])
    out = ok(TILTS)
    assert [c["id"] for c in out["classes"]] == ["cash", "bond", "equity", "gold"] and out["tilts"] == []
    assert [s["id"] for s in out["stances"]] == ["overweight", "neutral", "underweight"]
    ok(TILT, asset_class="gold", stance="overweight", view_id="V-1", by="cio")
    out = ok(TILTS)
    assert [(t["asset_class"], t["view_id"]) for t in out["tilts"]] == [("gold", "V-1")]
    gold = out["model"][3]["classes"]["gold"]
    assert gold["tilt"] == pytest.approx(0.02) and gold["target"] == pytest.approx(gold["base"] + 0.02)


def test_an_rm_sends_the_actions_to_the_review_queue():
    out = ok(SEND, client_id="C01", by="rm01")
    item = store.review(out["review_id"])
    assert item["kind"] == "allocation" and item["client_id"] == "C01"
    assert len(item["data"]["option"]["actions"]) == out["actions"]
    assert [s["label"] for s in item["data"]["summary"]][:3] == ["Thanh khoản", "Di sản", "Tăng trưởng"]
    assert "$errors" in run(SEND, client_id="C01", by="nobody")


def test_the_example_is_the_one_the_fixtures_write():
    assert case()["id"] == "K-7F3A" and fixtures.market()["as_of"]


@pytest.mark.parametrize("cid", ["C01", "C02", "C03", "C04", "C05"])
def test_no_action_sells_a_legacy_asset_or_raises_the_risk_level(cid):
    """§13 rule 5 (AA-N3, AA-N4): a Di sản gap is talked over, never sold to fill; the level is the test's or the
    simulated one, never raised to reach a goal."""
    a = ok(FLOW, client_id=cid)["allocation"]
    assert a["risk"]["level"] == ops.risk_of(cid, a["risk"]["drawdown_limit"])["level"]
    for x in a["actions"]:
        assert not set(x.get("moves") or {}) & set(_engine.LEGACY), (cid, x["what"])
        assert x["bucket"] != "legacy" or (x["kind"] == "talk" and not x["moves"]), (cid, x["what"])

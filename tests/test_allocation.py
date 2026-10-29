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
    allocation_method_flow,
    allocation_override_flow,
    allocation_queue_flow,
    allocation_review_flow,
    allocation_send_flow,
    allocation_tilt_flow,
    allocation_tilts_flow,
)
from views.schema import forbidden_words
from wealth import fixtures, store
from wealth.money import TY, TR

FLOW = Operon(allocation_flow, params={"client_id": None, "scope": None, "method": None, "assumptions": None, "role": None, "whatif": None})
EXAMPLE = Operon(allocation_example_flow, params={"method": None, "assumptions": None, "role": None})
TILT = Operon(allocation_tilt_flow, params={"asset_class": None, "stance": None, "view_id": None, "by": None, "reason": None})
TILTS = Operon(allocation_tilts_flow, params={})
SEND = Operon(allocation_send_flow, params={"client_id": None, "by": None, "scope": None, "method": None, "assumptions": None})
REVIEW = Operon(allocation_review_flow, params={"item_id": None, "by": None, "decisions": None, "note": None})
QUEUE = Operon(allocation_queue_flow, params={})
METHOD = Operon(allocation_method_flow, params={"method": None, "by": None})
OVERRIDE = Operon(
    allocation_override_flow, params={"client_id": None, "key": None, "by": None, "bucket": None, "reason": None, "scope": None}
)


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
    assert ops.risk_of("C03", 0.30) == {"level": 2, "name": "Thận trọng", "source": "test", "at": "2026-10-01",
                                         "tolerance": "Thận trọng", "capacity": "Thận trọng"}


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
    assert item["status"] == "pending_cio" and [a["status"] for a in item["data"]["actions"]] == ["pending"] * out["actions"]


def test_the_cio_approves_each_action_and_the_client_sees_only_the_approved_ones():
    """Q-29: the RM sends, the CIO decides each action; the item waits until every action is decided."""
    sent = ok(SEND, client_id="C01", by="rm01")
    rid, n = sent["review_id"], sent["actions"]
    assert n >= 2
    assert rid in [r["id"] for r in ok(QUEUE)["waiting"]]
    from desk import reads as desk

    waits = lambda: [x for x in desk.cio()["decide"] if x["kind"] == "allocation" and x["id"] == rid]  # noqa: E731
    assert [x["route"] for x in waits()] == ["#/cio/phan-bo"]  # the desk lists it with the CIO's other decisions
    assert "$errors" in run(REVIEW, item_id=rid, by="rm01", decisions={"0": "approve"})  # the CIO's, not the RM's
    assert "$errors" in run(REVIEW, item_id=rid, by="cio", decisions={"0": "maybe"})
    half = ok(REVIEW, item_id=rid, by="cio", decisions={"0": "approve"})["item"]
    assert half["status"] == "pending_cio"
    rest = {str(i): "reject" for i in range(1, n)}
    done = ok(REVIEW, item_id=rid, by="cio", decisions=rest, note="giữ việc đầu")["item"]
    assert done["status"] == "approved" and done["note"] == "giữ việc đầu"
    assert done["data"]["option"]["actions"] == [half["data"]["actions"][0]["what"]]
    assert "$errors" in run(REVIEW, item_id=rid, by="cio", decisions={"0": "reject"})  # decided once
    assert rid in [r["id"] for r in ok(QUEUE)["decided"]] and rid not in [r["id"] for r in ok(QUEUE)["waiting"]]
    assert not waits()
    none = ok(SEND, client_id="C01", by="rm01")
    out = ok(REVIEW, item_id=none["review_id"], by="cio", decisions={str(i): "reject" for i in range(none["actions"])})
    assert out["item"]["status"] == "rejected"


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


def test_an_rm_moves_an_asset_to_another_bucket_with_a_reason_and_the_cio_sees_it():
    """§5: the RM overrides one asset's bucket with a reason; the log is the CIO's to read (Compliance's desk)."""
    before = ok(FLOW, client_id="C01")["allocation"]
    h = max(before["buckets"]["growth"]["holdings"], key=lambda x: x["value"])
    args = dict(client_id="C01", key=h["key"], bucket="legacy")
    assert "$errors" in run(OVERRIDE, **args, by="rm01", reason="ngắn")  # a reason of 10 characters at least
    assert "$errors" in run(OVERRIDE, **args, by="cio", reason="giữ để lại cho con")  # the RM's
    assert "$errors" in run(OVERRIDE, **{**args, "bucket": "growth"}, by="rm01", reason="đã ở giỏ này rồi")
    got = ok(OVERRIDE, **args, by="rm01", reason="khách giữ để lại cho con")["override"]
    assert (got["from"], got["to"]) == ("growth", "legacy")
    after = ok(FLOW, client_id="C01")["allocation"]
    assert after["buckets"]["legacy"]["value"] == pytest.approx(before["buckets"]["legacy"]["value"] + h["value"])
    assert after["buckets"]["growth"]["value"] == pytest.approx(before["buckets"]["growth"]["value"] - h["value"])
    moved = next(x for x in after["buckets"]["legacy"]["holdings"] if x["key"] == h["key"])
    assert moved["moved"]["reason"] == "khách giữ để lại cho con"
    assert after["reconcile"]["buckets"] == pytest.approx(before["reconcile"]["buckets"])
    log = ok(QUEUE)["overrides"][0]
    assert (log["key"], log["to_label"], log["by"]) == (h["key"], "Di sản", "rm01")
    back = ok(OVERRIDE, client_id="C01", key=h["key"], bucket="", by="rm01")["override"]  # taken away
    assert (back["from"], back["to"]) == ("legacy", "growth")
    assert ok(FLOW, client_id="C01")["allocation"]["buckets"]["growth"]["value"] == pytest.approx(before["buckets"]["growth"]["value"])


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_black_litterman_reads_the_tilts_as_views_inside_the_cios_guards(level):
    """§15 P2: no view gives the level's model; a view moves its class the same way as the tilt, at most ±5 points,
    inside the range, and the model still sums to 100 %."""
    plain = _model.black_litterman(level, [])["classes"]
    assert all(v["target"] == pytest.approx(v["base"]) for v in plain.values())
    for c, stance in (("equity", "overweight"), ("bond", "overweight"), ("gold", "underweight")):
        t = [{"asset_class": c, "stance": stance, "view": "v"}]
        tilt, bl = _model.tilted(level, t)["classes"], _model.black_litterman(level, t)["classes"]
        assert sum(v["target"] for v in bl.values()) == pytest.approx(1.0)
        for k, v in bl.items():
            assert v["low"] - 1e-9 <= v["target"] <= v["high"] + 1e-9 and abs(v["tilt"]) <= 0.05 + 1e-9, (c, k)
        if tilt[c]["tilt"]:  # the tilt could move the class: Black–Litterman moves it the same way
            assert (bl[c]["tilt"] > 0) == (tilt[c]["tilt"] > 0), (c, bl[c], tilt[c])


def test_the_cio_picks_black_litterman_and_every_clients_model_follows(monkeypatch):
    from views import store as views

    monkeypatch.setattr(views, "approved", lambda: [{"id": "V-1", "current": {"summary": "Lãi suất giảm"}}])
    ok(TILT, asset_class="equity", stance="overweight", view_id="V-1", by="cio")
    try:
        assert "$errors" in run(METHOD, method="bl", by="rm01") and "$errors" in run(METHOD, method="x", by="cio")
        out = ok(TILTS)
        assert out["method"] == "tilt" and [m["id"] for m in out["methods"]] == ["tilt", "bl"]
        lv = ok(FLOW, client_id="C01")["allocation"]["risk"]["level"]
        assert ok(FLOW, client_id="C01")["allocation"]["model"]["method"] == "tilt"
        ok(METHOD, method="bl", by="cio")
        a = ok(FLOW, client_id="C01")["allocation"]
        assert a["model"]["method"] == "bl"
        assert a["model"]["classes"]["equity"]["target"] == pytest.approx(out["model_bl"][lv]["classes"]["equity"]["target"])
        assert ok(TILTS)["method"] == "bl"
    finally:
        ok(METHOD, method="tilt", by="cio")
        ok(TILT, asset_class="equity", stance="neutral", view_id="V-1", by="cio")


def test_eleven_classes_read_the_same_household_and_split_the_growth_model():
    """P2: the 11 asset classes are a second view of the household — they add up to its assets with what none of them
    is, and their Growth targets are the model's own targets split by the CIO's eleven.split."""
    for cid in ("C01", "C03"):
        a = ok(FLOW, client_id=cid, scope="family", role="rm01")["allocation"]
        e = a["eleven"]
        assert [r["key"] for r in e["rows"]] == list(_model.ELEVEN)
        assets = sum(r["value"] for r in e["rows"] if not r["loan"]) + e["outside"]
        assert abs(assets - a["reconcile"]["assets"]) < 1
        split = sum(r["target_pct"] or 0 for r in e["rows"])
        held = sum(m["target"] for c, m in a["model"]["classes"].items() if c in _model.data()["eleven"]["split"])
        assert abs(split - held) < 1e-6
    rows = {r["key"]: r for r in ok(FLOW, client_id="C01", scope="family", role="rm01")["allocation"]["eleven"]["rows"]}
    assert rows["real_estate"]["target_pct"] is None and rows["real_estate"]["value"] > 0
    assert rows["floating_loan"]["loan"] and rows["floating_loan"]["value"] > 0


def test_a_holding_finds_its_eleven_class_from_its_detail():
    def h(cls, kind="asset", **detail):
        return {"class": cls, "kind": kind, "detail": detail}

    assert _model.eleven_class(h("stock", ticker="FPT")) == "vn_equity"
    assert _model.eleven_class(h("stock", ticker="AAPL", market="US", currency="USD")) == "foreign_equity"
    assert _model.eleven_class(h("cash", currency="USD")) == "fx"
    assert _model.eleven_class(h("deposit")) is None
    assert _model.eleven_class(h("fund", fund_type="money")) is None
    assert _model.eleven_class(h("fund", fund_type="bond")) == "fund"
    assert _model.eleven_class(h("business")) == "private_equity"
    assert _model.eleven_class(h("loan", "liability", currency="USD")) == "usd_loan"
    assert _model.eleven_class(h("loan", "liability", rate_type="floating")) == "floating_loan"
    assert _model.eleven_class(h("loan", "liability", rate_type="fixed")) is None


# ── Chỉnh UI-UX ver2: a dated inflow, the what-if, the Legacy options ─────


def test_a_dated_inflow_counts_with_all_income_never_as_certain():
    c = case()
    base = _engine.allocate(c, "B")["cashflow"]
    c["profile"]["events"] = c["profile"]["events"] + [{"date": "2027-01-20", "direction": "in", "amount": 2 * TY, "label": "Thưởng"}]
    more = _engine.allocate(c, "B")["cashflow"]
    assert more["dated_in"][0]["label"] == "Thưởng" and more["targets"]["A"] == base["targets"]["A"]
    assert more["targets"]["C"] == base["targets"]["C"] and more["targets"]["B"] <= base["targets"]["B"]
    assert sum(y["income"] for y in more["years"]) == sum(y["income"] for y in base["years"]) + 2 * TY


def test_a_what_if_keeps_the_moved_money_in_liquidity_and_says_what_it_costs_growth():
    a = ok(FLOW, client_id="C01", scope="family", method="C")["allocation"]
    b = ok(FLOW, client_id="C01", scope="family", method="C", whatif={"move": 500 * TR})["allocation"]
    assert b["whatif"] == {"move": 500 * TR}
    assert b["liquidity"]["have"] == a["liquidity"]["have"] + 500 * TR
    assert round(a["growth"]["rebalance"]["total"] - b["growth"]["rebalance"]["total"]) == 500 * TR  # not swept back
    assert b["retirement"]["reach"] < a["retirement"]["reach"]
    less = ok(FLOW, client_id="C01", scope="family", method="C", whatif={"spending_change": -10 * TR})["allocation"]
    assert less["retirement"]["short"] < a["retirement"]["short"] and less["legacy"]["gap"] < a["legacy"]["gap"]
    assert "không có thay đổi" in str(run(FLOW, client_id="C01", whatif={"nope": 1})["$errors"])


def test_the_legacy_gap_comes_with_four_ways_to_close_it(k7):
    leg = k7["legacy"]
    assert leg["estate"] > 0 and leg["years"] >= 0
    if leg["gap"] > 0:
        o = {x["id"]: x for x in leg["options"]}
        assert list(o) == ["keep", "save", "insure", "mix"]
        assert o["keep"]["monthly"] == 0 and o["insure"]["left_now"] == 0 and o["save"]["left_now"] > 0
        assert o["insure"]["monthly"] < o["save"]["monthly"] < o["mix"]["monthly"]

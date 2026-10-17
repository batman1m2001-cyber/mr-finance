"""The overview's money flows (UNIFIED_FLOWS_PLAN F1–F3, F11; OWN-GW-34…38, 49): every money edge says its amount,
its monthly rate and which way the money goes; relations carry none; the month's categories sum to the totals; a
goal's edge is the monthly saving it needs, and goals counting the same pool say so; a news edge's monthly rate is its
3-month change over its own horizon; a policy item gets an amount only where one class takes it; another family
member's holdings are marked. Nothing is invented: each figure is checked against the record it came from."""

import asyncio

from operonx import Operon
from test_apply import MARKET, approved

from apply import reads
from impact.graph import alerts_flow
from overview.graph import overview_flow
from scenarios.graph import goals_flow

OV = Operon(overview_flow, params={"client_id": None, "scope": None, "role": None, "goals": None})


def overview(**inputs):
    out = asyncio.run(OV.run(inputs={"client_id": "C01", **inputs}))
    assert "$errors" not in out, out["$errors"]
    return out["overview"]


def by_id(o):
    return {n["id"]: n for n in o["nodes"]}, {(e["from"], e["to"]): e for e in o["edges"]}


def test_money_edges_say_how_much_a_month_and_which_way_relations_say_nothing():
    approved(*MARKET)
    o = overview()
    nodes, edges = by_id(o)
    assert edges[("FL:in", "ME")]["monthly"] == nodes["FL:in"]["value"] and edges[("FL:in", "ME")]["dir"] == "fwd"
    assert edges[("ME", "FL:out")]["monthly"] == nodes["FL:out"]["value"] and edges[("ME", "FL:out")]["dir"] == "fwd"
    for e in o["edges"]:
        if e["value"] is None:
            assert "monthly" not in e and "dir" not in e, e  # a relation: no amount, so nothing to move
        if "dir" in e:
            assert e["dir"] in ("fwd", "back") and e["value"] is not None


def test_the_months_categories_add_up_and_open_from_their_side():
    o = overview()
    nodes, edges = by_id(o)
    for side, fid in (("in", "FL:in"), ("out", "FL:out")):
        cats = [n for n in o["nodes"] if n["kind"] == "category" and n["side"] == side]
        assert cats and all(n["parent"] == fid and n["rows"] > 0 for n in cats)
        assert sum(n["value"] for n in cats) == nodes[fid]["value"]
        for n in cats:
            e = edges[(n["id"], fid)] if side == "in" else edges[(fid, n["id"])]
            assert e["parent"] == fid and e["monthly"] == n["value"] and e["certainty"] == "actual"
            assert f"flow:{n['month']}:{side}:{n['ref']}" in n["keys"]


def test_a_goal_edge_is_the_monthly_saving_it_needs_and_shared_pools_are_said_once():
    o = overview()
    nodes, edges = by_id(o)
    out = asyncio.run(Operon(goals_flow, params={"client_id": None, "scope": None}).run(inputs={"client_id": "C01"}))
    goals = {g["id"]: g["goal"] for g in out["goals"]}
    shown = [n for n in o["nodes"] if n["kind"] == "goal"]
    for n in shown:
        g, e = goals[n["ref"]], edges[("ME", n["id"])]
        assert e["certainty"] == "estimate"
        if g["gap"] > 0 and (g["monthly"] or 0) > 0:
            assert e["value"] == e["monthly"] == g["monthly"] and e["dir"] == "fwd"
            assert e["label"] == "cần để dành/tháng"
        else:
            assert e["value"] is None  # enough already, or no source to close it: nothing to move
    pools = {}
    for n in shown:
        if n.get("pool"):
            pools.setdefault(n["pool"]["have"], set()).add(n["id"])
            assert edges[("ME", n["id"])]["shared"] is True
    assert pools, "C01's goals count the same liquid pool"
    for have, ids in pools.items():
        assert len(ids) >= 2 and all(round(nodes[i]["have"]) == have for i in ids)
        assert all(set(nodes[i]["pool"]["goals"]) == ids for i in ids)
    need = sum(goals[n["ref"]]["monthly"] or 0 for n in shown if goals[n["ref"]]["gap"] > 0)
    assert nodes["ME"]["goal_monthly"] == need and nodes["ME"]["surplus"] == goals[shown[0]["ref"]]["surplus"]


def test_a_news_edge_moves_its_three_month_change_over_three_months_and_keeps_its_band():
    approved(*MARKET)
    o = overview()
    nodes, edges = by_id(o)
    runs = {i["run_id"]: i for i in reads.family_impact("C01", "client")["items"] if i["status"] == "EFFECTIVE"}
    evs = [n for n in o["nodes"] if n["kind"] == "event"]
    assert evs
    for n in evs:
        h3 = runs[n["run"]]["horizons"]["3m"]
        assert n["band"] == {k: h3[k] for k in ("p10", "p50", "p90")} and n["horizon"] == "3m"
        assert n["modelled_share"] == runs[n["run"]]["modelled_share"]
        for (a, b), e in edges.items():
            if a == n["id"]:
                assert e["monthly"] == abs(e["value"]) / 3 and e["dir"] == ("fwd" if e["value"] > 0 else "back")


def _policy_edges(o):
    """Each policy item's class-level edges (or its edge to the client)."""
    return {
        n["ref"]: [e for e in o["edges"] if e["to"] == n["id"] and not e["from"].startswith("HD:")]
        for n in o["nodes"]
        if n["kind"] == "alert"
    }


def test_a_policy_item_has_an_amount_only_where_one_class_takes_it(monkeypatch):
    rep = asyncio.run(Operon(alerts_flow, params={"client_id": None, "scope": None}).run(inputs={"client_id": "C01"}))
    impact = {a["id"]: a["impact"] for a in rep["report"]["alerts"]}
    for ref, level in _policy_edges(overview()).items():  # every item of the demo data touches one class
        assert len({e["from"] for e in level}) == 1
        assert level[0]["value"] == impact[ref] and level[0]["dir"] == ("back" if impact[ref] > 0 else "fwd")
    # an item naming holdings of two classes: its total has no split, so its edges get no amount
    from impact import _rules
    from wealth import fixtures

    held = {n["parent"]: n["label"] for n in overview()["nodes"] if n["kind"] == "holding"}
    names = [held["CL:stock"], held["CL:real_estate"]]
    hit = {"raw": -2e8, "exposure": 1e9, "sensitivity": 0.2, "message": "x", "affected": names}
    monkeypatch.setitem(_rules.RULES, "two_classes", lambda *a: [hit])
    real = fixtures.factors()
    extra = {**real["factors"][0], "id": "TWO", "rule": {"type": "two_classes"}, "probability": 1.0}
    monkeypatch.setattr(fixtures, "factors", lambda: {**real, "factors": real["factors"] + [extra]})
    level = _policy_edges(overview())["TWO-0"]
    assert {e["from"] for e in level} == {"CL:stock", "CL:real_estate"}
    assert all(e["value"] is None and "dir" not in e for e in level), level


def test_another_family_members_holdings_are_marked():
    mine = [n for n in overview()["nodes"] if n["kind"] == "holding"]
    assert mine and not any(n["family"] for n in mine)
    fam = [n for n in overview(scope="family")["nodes"] if n["kind"] in ("holding", "category")]
    marked = {n["owner"] for n in fam if n["kind"] == "holding" and n["family"]}
    assert marked and "Nguyễn Minh Khoa" not in marked

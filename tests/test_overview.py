"""The overview graph (src/overview, UI redesign R4): every node and edge is read from a record another page shows —
a holding, the dashboard's risk, a goal, a policy item, an EFFECTIVE run — and the edge names it; the classes add up
to the net worth; the client reads events by type; the goals followed are the ones the browser sends."""

import asyncio

from operonx import Operon
from test_apply import MARKET, approved

from apply import reads
from overview.graph import overview_flow

OV = Operon(overview_flow, params={"client_id": None, "scope": None, "role": None, "goals": None})


def overview(**inputs):
    out = asyncio.run(OV.run(inputs={"client_id": "C01", **inputs}))
    assert "$errors" not in out, out["$errors"]
    return out["overview"]


def dashboard(client_id="C01"):
    from dashboard.graph import dashboard_flow

    out = asyncio.run(
        Operon(dashboard_flow, params={"client_id": None, "scope": None, "months": None}).run(
            inputs={"client_id": client_id}
        )
    )
    return out["dashboard"]


def test_every_edge_comes_from_a_record_it_names():
    approved(*MARKET)
    o = overview(role="rm")
    d = dashboard()
    from impact.graph import alerts_flow

    rep = asyncio.run(Operon(alerts_flow, params={"client_id": None, "scope": None}).run(inputs={"client_id": "C01"}))
    alerts = {a["id"]: a for a in rep["report"]["alerts"]}
    holdings = {h["key"]: h for h in d["holdings"]}
    runs = {i["run_id"]: i for i in reads.family_impact("C01", "rm")["items"] if i["status"] == "EFFECTIVE"}
    ids = {n["id"] for n in o["nodes"]}
    assert runs, "the seeded run is effective"
    for e in o["edges"]:
        assert e["from"] in ids and e["to"] in ids, e
        assert e["sources"], e
        for s in e["sources"]:
            if s["type"] == "holding":
                assert s["id"] in holdings, s
            elif s["type"] == "risk":
                assert s["id"] in ("drawdown", "concentration", "liquidity"), s
            elif s["type"] == "goal":
                assert e["to"] == f"GL:{s['id']}"
            elif s["type"] == "alert":
                a = alerts[s["id"]]
                if e["from"].startswith("HD:"):  # joined by a name the policy item lists
                    assert holdings[e["from"][3:]]["name"] in a["affected"]
            elif s["type"] == "run":
                cls = e["to"][3:]
                assert e["value"] == sum(
                    v for c, v in runs[s["id"]]["by_class"].items() if (c if c != "cash" else "deposit") == cls
                )
                assert e["label"] == "có thể ảnh hưởng"
            elif s["type"] == "txn":  # the month's money in or out (FEAT-40); a debt it repaid carries the amount
                if e["from"] in ("CL:loan", "CL:card"):
                    out = next(n for n in o["nodes"] if n["id"] == "FL:out")
                    cat = e["from"][3:]
                    assert e["repaid"] == sum(i["value"] for i in out["items"] if i["category"] == cat) > 0, e
                else:
                    assert "FL:in" in (e["from"], e["to"]) or "FL:out" in (e["from"], e["to"]), e
            elif s["type"] == "scenario":
                assert e["to"] == f"SC:{s['id']}" and e["value"] is None, e
            else:
                raise AssertionError(s)


def test_the_classes_add_up_to_the_net_worth_and_open_onto_their_holdings():
    o = overview()
    d = dashboard()
    out = sum(e["value"] for e in o["edges"] if e["from"] == "ME" and e["to"].startswith("CL:"))
    debt = sum(e["value"] for e in o["edges"] if e["to"] == "ME" and e["from"].startswith("CL:"))
    assert out == d["net_worth"]["assets"] and debt == d["net_worth"]["liabilities"]
    kids = [n for n in o["nodes"] if n["kind"] == "holding"]
    assert len(kids) == len([h for h in d["holdings"] if h["value"]])
    for n in kids:  # a holding edge is drawn only when its class is open; the class edge otherwise
        assert any(e.get("parent") == n["parent"] and n["id"] in (e["from"], e["to"]) for e in o["edges"])
    for e in o["edges"]:
        assert not ("parent" in e and "agg" in e)


def test_the_client_reads_the_event_type_and_staff_the_headline():
    approved(*MARKET)
    client = [n for n in overview()["nodes"] if n["kind"] == "event"]
    staff = [n for n in overview(role="rm")["nodes"] if n["kind"] == "event"]
    assert len(client) == len(staff) == 1
    assert client[0]["label"] == reads.family_impact("C01", "client")["items"][0]["event"]["title"]
    assert client[0]["label"] != staff[0]["label"]
    assert "Bạn" == next(n["label"] for n in overview()["nodes"] if n["kind"] == "family")


def test_the_goals_are_the_ones_the_browser_follows():
    default = {n["ref"] for n in overview()["nodes"] if n["kind"] == "goal"}
    assert default
    picked = {n["ref"] for n in overview(goals=["retire_early"])["nodes"] if n["kind"] == "goal"}
    assert picked == {"retire_early"}
    assert not [n for n in overview(goals=[])["nodes"] if n["kind"] == "goal"]


def test_the_workspace_kinds_money_reserve_and_scenarios():
    # FEAT-40 (OWN-GW-11/12): the month's flows as on Toàn cảnh, the reserve always, the stress scenarios hypothetical
    from flows.graph import flows_flow

    o = overview()
    by = {n["id"]: n for n in o["nodes"]}
    f = asyncio.run(
        Operon(flows_flow, params={"client_id": None, "scope": None, "month": None}).run(inputs={"client_id": "C01"})
    )
    f = f["flows"]
    assert by["FL:in"]["value"] == f["total_in"] and by["FL:out"]["value"] == f["total_out"]
    assert by["FL:in"]["month"] == f["month"] and f"flow:{f['month']}" in by["FL:out"]["keys"]
    top = max(f["outflow"], key=lambda b: b["amount"])
    assert f"flow:{f['month']}:out:{top['category']}" in by["FL:out"]["keys"]  # the flows answer's focus key lights it
    d = dashboard()
    assert by["LQ:reserve"]["value"] == d["liquidity"]["value"]
    scen = [n for n in o["nodes"] if n["kind"] == "scenario"]
    assert scen and all(n["value"] is None for n in scen)
    cert = {(e["from"], e["to"]): e["certainty"] for e in o["edges"]}
    assert all(cert[("ME", n["id"])] == "hypothetical" for n in scen)
    assert cert[("FL:in", "ME")] == cert[("ME", "LQ:reserve")] == "actual"
    assert all(
        cert[(e["from"], e["to"])] == "estimate"
        for e in o["edges"]
        if e["from"].startswith(("EV:", "AL:")) or e["to"].startswith("AL:")
    )
    # a scenario is never part of net worth: the classes still add up without it
    assert (
        sum(e["value"] for e in o["edges"] if e["from"] == "ME" and e["to"].startswith("CL:"))
        == d["net_worth"]["assets"]
    )
    assert {k["kind"] for k in o["kinds"]} >= {"flow", "liquidity", "scenario"}

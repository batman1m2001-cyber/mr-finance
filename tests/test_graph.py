"""The Financial Intelligence Graph (src/apply/impact_graph.py, kit K3): a view over stored records."""

from starlette.testclient import TestClient
from test_apply import MARKET, approved

from apply import run as runs
from apply.impact_graph import family_graph
from events import store as events
from views import store as vstore


def resolves(src):
    if src["type"] == "event":
        return events.get(src["id"]) is not None
    if src["type"] == "view":
        return vstore.get(src["id"]) is not None
    if src["type"] == "run":
        return runs.get(src["id"])["status"] == "EFFECTIVE"
    return False


def test_every_edge_comes_from_a_stored_record_and_the_columns_chain():
    _, run = approved(*MARKET)
    g = family_graph("C01", "rm")
    ids = {n["id"] for n in g["nodes"]}
    kinds = {n["id"]: n["kind"] for n in g["nodes"]}
    order = [c["kind"] for c in g["columns"]]
    assert g["edges"] and all(e["from"] in ids and e["to"] in ids for e in g["edges"])
    for e in g["edges"]:
        assert e["sources"] and all(resolves(s) for s in e["sources"]), e
        assert order.index(kinds[e["to"]]) == order.index(kinds[e["from"]]) + 1  # left to right, one column a step
    assert {"news", "event", "branch", "factor", "asset", "family", "goal"} <= set(kinds.values())
    # the asset → family edges add up to the run's 3-month expected change for the shown holdings
    fam = runs.family_result(run["id"], "C01")["horizons"]["3m"]
    to_family = [e for e in g["edges"] if e["to"] == "FAM:C01"]
    assert all(e["value"] == fam["by_holding"][e["from"][3:]] for e in to_family)


def test_the_client_sees_no_headline_and_no_holding():
    approved(*MARKET)
    staff, client = family_graph("C01", "rm"), family_graph("C01", "client")
    headlines = {n["label"] for n in staff["nodes"] if n["kind"] in ("news", "event")}
    holdings = {n["label"] for n in staff["nodes"] if n["kind"] == "asset"}
    labels = {n["label"] for n in client["nodes"]}
    assert headlines and not (headlines & labels)
    assert holdings and not (holdings & labels)
    assert all(n["id"].startswith("AC:") for n in client["nodes"] if n["kind"] == "asset")
    assert not any("url" in n for n in client["nodes"])


def test_no_effective_run_is_an_empty_graph_and_the_endpoint():
    assert family_graph("C01", "client")["nodes"] == []
    from app.web import app

    approved(*MARKET)
    c = TestClient(app)
    assert c.get("/api/families/C01/graph?role=rm").json()["edges"]
    assert c.get("/api/families/C01/graph?role=nobody").status_code == 403

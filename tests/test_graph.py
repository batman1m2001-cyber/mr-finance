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


def test_an_events_share_of_each_asset_adds_up_to_its_expected_change():
    # the News Impact panel (R4) reads each event's own share of an edge several runs add to
    _, run = approved(*MARKET)
    g = family_graph("C01", "client")
    ev = next(n for n in g["nodes"] if n["kind"] == "event")
    assert ev["run"] == run["id"]
    shares = [e["by_run"][run["id"]] for e in g["edges"] if e["to"] == "FAM:C01" and run["id"] in e.get("by_run", {})]
    fam = runs.family_result(run["id"], "C01")["horizons"]["3m"]
    assert round(sum(shares)) == round(sum(fam["by_class"].values())) == round(ev["expected_3m"])


def test_the_cio_run_graph_reaches_every_family_from_the_stored_results():
    from app.web import app
    from apply.impact_graph import run_graph

    _, run = approved(*MARKET)
    g = run_graph(run["id"])
    results = runs.family_results(run["id"])
    fams = [n for n in g["nodes"] if n["kind"] == "family"]
    assert g["families"] == len(results) == len(fams) and len(fams) > 1
    order = [c["kind"] for c in g["columns"]]
    kinds = {n["id"]: n["kind"] for n in g["nodes"]}
    for e in g["edges"]:
        assert e["sources"] and all(resolves(s) for s in e["sources"]), e
        assert order.index(kinds[e["to"]]) == order.index(kinds[e["from"]]) + 1
        if kinds[e["to"]] == "family":  # a class → family edge is that family's change by class
            assert e["value"] == results[e["to"][4:]]["horizons"]["3m"]["by_class"][e["from"][3:]]
    assert TestClient(app).get(f"/api/runs/{run['id']}/graph").json()["run_id"] == run["id"]
    assert TestClient(app).get("/api/runs/AR-nope/graph").status_code == 404


def test_the_timeline_reads_each_step_from_its_record():
    from apply import reads

    _, run = approved(*MARKET)
    item = reads.family_impact("C01", "client")["items"][0]
    tl = item["timeline"]
    assert [x["at"] for x in tl] == sorted(x["at"] for x in tl)
    ev = events.get(run["event_id"])
    view = vstore.get(run["view_id"])
    assert tl[0] == {
        "at": min(n["published"] for n in ev["news"]),
        "step": "news",
        "label": "Tin đầu tiên",
        "source": "event",
    }
    approved_at = next(h["at"] for h in view["history"] if h["status"] == "APPROVED")
    assert {"at": approved_at, "step": "approved", "label": "CIO duyệt", "source": "view"} in tl
    assert tl[-1]["step"] == "effective" and tl[-1]["at"] == runs.get(run["id"])["history"][-1]["at"]

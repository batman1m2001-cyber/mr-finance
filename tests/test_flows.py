"""Money Flow (src/flows, redesign kit K2): bands are the transaction rows, summed to the dong."""

import asyncio

from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient

from flows.graph import flows_flow
from wealth import fixtures

FLOWS = Operon(flows_flow, params={"client_id": None, "scope": None, "month": None})


def run(**inputs):
    return asyncio.run(FLOWS.run(inputs=inputs))


def tx(cid):
    return fixtures.client(cid)["sources"]["techcombank"]["transactions"]


def test_the_bands_are_the_transactions_of_the_month_to_the_dong():
    f = run(client_id="C01", month="2026-09")["flows"]
    rows = [t for t in tx("C01") if t["date"].startswith("2026-09")]
    assert f["total_in"] == sum(t["amount"] for t in rows if t["direction"] == "in")
    assert f["total_out"] == sum(t["amount"] for t in rows if t["direction"] == "out")
    assert f["left"] == f["total_in"] - f["total_out"]
    for side in ("inflow", "outflow"):
        for b in f[side]:
            assert b["amount"] == sum(r["amount"] for r in b["rows"])  # a band opens to its rows
    assert sum(len(b["rows"]) for b in f["inflow"] + f["outflow"]) == len(rows) == f["rows"]
    # C01, Sep 2026 (plan fact F6): salary 120.4 tr in; living, card and the home loan out; 30.0 tr left
    assert [b["category"] for b in f["inflow"]] == ["salary"]
    assert {b["category"] for b in f["outflow"]} == {"living", "card", "loan"}
    assert round(f["left"] / 1e6, 1) == 30.0


def test_the_latest_month_by_default_and_the_family_adds_the_spouse():
    me = run(client_id="C01")["flows"]
    assert me["month"] == me["months"][-1] == max(t["date"] for t in tx("C01"))[:7]
    fam = run(client_id="C01", scope="family", month=me["month"])["flows"]
    assert fam["total_in"] > me["total_in"] and len(fam["members"]) == 2
    assert {r["owner"] for b in fam["inflow"] for r in b["rows"]} == {"C01", "C01S"}


def test_a_month_without_rows_or_a_bad_request_is_refused():
    for bad in ({"client_id": "C01", "month": "2020-01"}, {"client_id": "C01", "month": "9/2026"}, {"client_id": "X"}):
        assert "$errors" in run(**bad)


def test_the_endpoint():
    with TestClient(Application.find(".").asgi()) as client:
        r = client.post("/api/flows", json={"client_id": "C03", "scope": "personal"})
        assert r.status_code == 200 and r.json()["flows"]["outflow"]

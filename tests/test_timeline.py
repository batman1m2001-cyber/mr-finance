"""A node's money over time (src/timeline, docs/NODE_TIMELINE_PLAN.md): the simulated history ends at today's figures
and passes the anchors the app already counts; the overview's month change is today's value − prev_value, as on Tổng
quan; the reads add up (classes to net worth, family over personal); money in and out are the rows' sums."""

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

import pytest
from operonx import Operon

from overview.graph import overview_flow
from timeline.graph import timeline_flow
from timeline.history import grid, month_back
from wealth.paths import DATA

ROOT = Path(__file__).resolve().parents[1]
PEOPLE = sorted(p.stem for p in (DATA / "clients").glob("*.json"))
TL = Operon(timeline_flow, params={"client_id": None, "scope": None, "node": None, "unit": None})
OV = Operon(overview_flow, params={"client_id": None, "scope": None, "role": None, "goals": None})


def timeline(**inputs):
    out = asyncio.run(TL.run(inputs={"client_id": "C01", **inputs}))
    assert "$errors" not in out, out.get("$errors")
    return out["timeline"]


def overview(**inputs):
    out = asyncio.run(OV.run(inputs={"client_id": "C01", "role": "client", **inputs}))
    assert "$errors" not in out, out.get("$errors")
    return out["overview"]


def today_holdings(person):
    sys.path.insert(0, str(ROOT / "scripts"))
    import make_history

    market = json.loads((DATA / "market.json").read_text(encoding="utf-8"))
    client = json.loads((DATA / "clients" / f"{person}.json").read_text(encoding="utf-8"))
    return make_history.holdings_of(client, market)


@pytest.mark.parametrize("person", PEOPLE)
def test_every_history_ends_at_today_and_passes_the_anchors(person):
    doc = json.loads((DATA / "history" / f"{person}.json").read_text(encoding="utf-8"))
    as_of = date.fromisoformat(doc["as_of"])
    assert doc["dates"] == [d.isoformat() for d in grid(as_of)]  # one grid for everyone (history.grid)
    at = {d: i for i, d in enumerate(doc["dates"])}
    t1, jan = month_back(as_of).isoformat(), f"{as_of.year}-01-01"
    for h in today_holdings(person):
        v = doc["holdings"][h["key"]]["values"]
        assert min(v) >= 0, h["key"]
        assert abs(v[at[doc["as_of"]]] - h["value"]) <= 1_000, h["key"]
        assert abs(v[at[t1]] - h["prev_value"]) <= 1_000, h["key"]
        bought = h["detail"].get("bought")
        if h["ytd_value"] is not None and not (bought and bought > jan):  # one bought since was not held on 1 January
            assert abs(v[at[jan]] - h["ytd_value"]) <= 1_000, h["key"]
    for c in doc["closed"].values():
        assert min(c["values"]) >= 0 and c["values"][at[t1]] == 0  # spent on today's holdings before the anchor
    assert all(r["date"] < "2025-10-01" for r in doc["transactions"])  # only before the fixtures' months


def test_the_month_change_is_tong_quans_and_the_classes_add_up_to_net_worth():
    ov = overview()
    nodes = {n["id"]: n for n in ov["nodes"]}
    me = nodes["ME"]
    holdings = [n for n in ov["nodes"] if n["kind"] == "holding"]
    from dashboard.graph import dashboard_flow

    dash = asyncio.run(
        Operon(dashboard_flow, params={"client_id": None, "scope": None, "months": None}).run(
            inputs={"client_id": "C01"}
        )
    )["dashboard"]
    assert me["change"]["month"] == pytest.approx(dash["net_worth"]["month_change"], abs=5_000)
    classes = [n for n in ov["nodes"] if n["kind"] == "class"]
    for unit in ("day", "month", "year"):
        total = sum((-1 if c["liability"] else 1) * c["change"][unit] for c in classes)
        assert total == pytest.approx(me["change"][unit], abs=len(holdings) * 1_000)
    assert all("change" in h for h in holdings)


def test_money_in_and_out_change_by_their_rows():
    ov = overview()
    nodes = {n["id"]: n for n in ov["nodes"]}
    assert nodes["FL:in"]["change"]["month"] == nodes["FL:in"]["value"]
    assert nodes["FL:out"]["change"]["month"] == -nodes["FL:out"]["value"]
    assert nodes["FL:in"]["change"]["year"] > nodes["FL:in"]["value"] * 11  # twelve months of salary


def test_a_timeline_by_day_month_and_year_ends_at_today():
    me = overview()["nodes"][0]
    assert me["id"] == "ME"
    for unit, n in (("day", 90), ("month", 70), ("year", 6)):
        t = timeline(node="ME", unit=unit)
        assert t["kind"] == "level" and t["simulated"] and len(t["points"]) == n
        assert t["points"][-1]["t"] == t["as_of"] == "2026-10-09"
        assert t["points"][-1]["value"] == pytest.approx(me["value"], abs=30_000)
        for a, b in zip(t["points"], t["points"][1:]):
            if unit != "day":
                assert b["change"] == pytest.approx(b["value"] - a["value"], abs=2)
    assert timeline(node="ME", unit="month")["points"][0]["label"] == "T1/21"


def test_the_family_holds_the_spouse_and_a_flow_is_its_sums():
    mine, ours = timeline(node="ME", unit="year"), timeline(node="ME", unit="year", scope="family")
    assert ours["points"][-1]["value"] > mine["points"][-1]["value"]
    out = timeline(node="FL:out", unit="month")
    assert out["kind"] == "flow" and out["points"][-1]["t"] == "2026-09" and out["points"][-1]["value"] < 0
    assert out["points"][0]["t"] == "2021-01" and out["points"][0]["value"] < 0  # the older rows
    debt = timeline(node="CL:loan", unit="year")
    assert debt["liability"] and debt["points"][0]["value"] > debt["points"][-1]["value"]  # paid down


def test_an_unknown_node_or_unit_is_refused():
    for bad in ({"node": "GL:x"}, {"unit": "week"}):
        out = asyncio.run(TL.run(inputs={"client_id": "C01", **bad}))
        assert "$errors" in out

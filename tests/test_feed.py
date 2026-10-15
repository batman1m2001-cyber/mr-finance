"""The Intelligence Feed (src/feed, kit K4): each item says why it is shown and points at its evidence."""

import asyncio

from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient
from test_apply import MARKET, approved

from apply import run as runs
from events import store as events
from feed import ops
from feed.graph import feed_flow

FEED = Operon(feed_flow, params={"client_id": None, "scope": None, "role": None})


def items(client_id="C01", role="rm"):
    out = asyncio.run(FEED.run(inputs={"client_id": client_id, "role": role}))
    assert "$errors" not in out, out["$errors"]
    return out["feed"]["items"]


def test_a_news_impact_shows_with_its_run_and_its_reason():
    _, run = approved(*MARKET)
    fam = runs.family_result(run["id"], "C01")
    got = [i for i in items() if i["type"] == "impact"]
    assert got, "the market fall reaches C01"
    for i in got:
        assert i["evidence"]["kind"] == "run" and runs.get(i["evidence"]["id"])["status"] == "EFFECTIVE"
        assert i["link"] == "impact" and i["why"]
    mine = next(i for i in got if i["evidence"]["id"] == run["id"])
    assert mine["value"] == fam["horizons"]["3m"]["expected"]
    assert abs(mine["value"]) >= ops.IMPACT_SHARE * fam["net_worth"] or fam["pre_review"]


def test_the_client_reads_the_event_type_not_the_headline():
    _, run = approved(*MARKET)
    title = events.get(run["event_id"])["title"]
    client = [i for i in items(role="client") if i["type"] == "impact"]
    assert client and not any(title in i["title"] for i in client)
    assert any(title in i["title"] for i in items(role="rm") if i["type"] == "impact")


def test_thresholds_and_a_spending_jump_carry_their_numbers():
    risk = [i for i in items() if i["type"] == "risk"]  # C01: 12.4 % against a 15 % limit is "near"
    assert risk and risk[0]["evidence"] == {"kind": "dashboard", "id": "risk"} and risk[0]["link"] == "detail"
    tx = [
        {"date": "2026-08-10", "amount": 10e6, "direction": "out", "category": "living"},
        {"date": "2026-09-10", "amount": 16e6, "direction": "out", "category": "living"},  # +60 %, +6 tr
        {"date": "2026-08-12", "amount": 10e6, "direction": "out", "category": "card"},
        {"date": "2026-09-12", "amount": 14e6, "direction": "out", "category": "card"},  # +40 % but +4 tr only
    ]
    [jump] = ops._spending(tx)
    assert jump["evidence"]["category"] == "living" and jump["value"] == -6e6 and jump["link"] == "flow"


def test_a_regulation_match_is_an_item_and_the_client_sees_only_its_message(monkeypatch):
    row = {
        "goal": "Học phí",
        "goal_id": "GL-C01-01",
        "level": "remind",
        "level_label": "Nhắc",
        "note_id": "RS-0001",
        "note_title": "Thông tư X",
        "milestone": "2026-12-07",
        "rm_hint": "Gọi khách",
        "client_message": None,
    }
    monkeypatch.setattr(ops.research, "matches", lambda fid: [row])
    assert [i["evidence"] for i in ops._regulation("C01", "rm")] == [
        {"kind": "regulation", "id": "RS-0001", "goal": "GL-C01-01"}
    ]
    assert ops._regulation("C01", "client") == []  # no client message: the RM confirms first


def test_nothing_to_show_is_an_empty_list_and_the_endpoint():
    calm = {
        "as_of": "2026-10-09",
        "net_worth": {"value": 1e9, "month_change": 0, "month_change_pct": 0.0},
        "risk": {"status": "ok"},
        "liquidity": {"status": "ok"},
    }
    assert ops.build("C03", "personal", "client", calm, [])["items"] == []
    with TestClient(Application.find(".").asgi()) as c:
        r = c.post("/api/feed", json={"client_id": "C01", "role": "client"})
        assert r.status_code == 200 and "items" in r.json()["feed"]

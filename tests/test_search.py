"""Header search (src/search, UI redesign R1): hits only among what the role may open, accent-insensitive, the
client never matched or shown a headline, each hit with its route."""

import asyncio

from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient
from test_apply import MARKET, approved

from events import store as events
from search.graph import search_flow

SEARCH = Operon(search_flow, params={"q": None, "role": None, "client_id": None, "scope": None})


def hits(q, role, client_id="C01"):
    out = asyncio.run(SEARCH.run(inputs={"q": q, "role": role, "client_id": client_id}))
    assert "$errors" not in out, out["$errors"]
    return out["search"]["hits"]


def test_holdings_and_goals_accent_insensitive_with_their_pages():
    got = hits("vang", "client")
    gold = next(h for h in got if h["kind"] == "holding")
    assert gold["label"] == "Vàng miếng SJC" and gold["route"] == "#/client/tai-san" and gold["value"] > 0
    assert [h["kind"] for h in hits("hoc phi", "client")] == ["goal"]
    assert hits("Học phí", "rm")[0]["route"] == "#/rm/khach-hang/ke-hoach"
    assert hits("v", "client") == []  # one letter: nothing


def test_whole_words_rank_first_and_the_rm_finds_clients():
    got = hits("khoa", "rm")
    assert got[0]["kind"] == "client" and got[0]["client_id"] == "C01"  # the name, before “khoản”
    assert not [h for h in hits("khoa", "client") if h["kind"] == "client"]


def test_the_client_never_matches_a_headline_staff_do():
    _, run = approved(*MARKET)
    ev = events.get(run["event_id"])
    word = "khối ngoại"  # in the headline only
    assert word in ev["title"].lower()
    assert not hits(word, "client")
    assert [h["ref"] for h in hits(word, "rm") if h["kind"] == "event"] == [ev["id"]]
    cio = [h for h in hits(word, "cio") if h["kind"] == "event"]
    assert cio[0]["route"] == f"#/cio/nhan-dinh/{ev['id']}"
    client = [h for h in hits("thi truong", "client") if h["kind"] == "event"]
    assert client and all(h["ref"] == "" and h["label"] != ev["title"] for h in client)  # the type label only


def test_news_and_research_stay_with_staff():
    approved(*MARKET)
    assert [h for h in hits("VN-Index", "cio") if h["kind"] == "news"]
    for role in ("client", "rm"):
        assert not [h for h in hits("VN-Index", role) if h["kind"] in ("news", "research")]
    assert not [h for h in hits("VN-Index", "compliance") if h["kind"] == "news"]  # nothing held


def test_bad_requests_and_the_endpoint():
    out = asyncio.run(SEARCH.run(inputs={"q": "x" * 81, "role": "client", "client_id": "C01"}))
    assert "$errors" in out
    out = asyncio.run(SEARCH.run(inputs={"q": "vang", "role": "admin", "client_id": "C01"}))
    assert "$errors" in out
    with TestClient(Application.find(".").asgi()) as c:
        r = c.post("/api/search", json={"q": "vàng", "role": "client", "client_id": "C01"})
        assert r.status_code == 200 and r.json()["search"]["hits"][0]["label"] == "Vàng miếng SJC"

"""The AI zone (BRD §5, ZONE-01…06, LC-04, SEC-07; F-D7; BRD completion F6): a second process with its own SQLite
file. TCB sends it the approved catalogues and released research (signed); it fetches the same public feeds on its
own, runs the CIO agent, and pushes the view to TCB's write-only inbox (signed), where the import checks it again.

Both sides run here in one process: ``zone()`` switches the state file and ``MF_ZONE`` the way app/zone.py runs."""

import asyncio
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest
from operonx.app import Application
from starlette.testclient import TestClient
from test_views import INGEST, NOW, ok

from control import config, db, roles
from inbox import importer, sign
from news import store as news_store
from people import store as people
from views import store as vstore
from wealth.paths import OutsideTheZone
from zone import agent, mirror, sync
from zone import web as zone_web

INBOX_KEY, ZONE_KEY = "khoa-hop-cho", "khoa-vung-ai"
GOLD = [("Giá vàng thế giới giảm mạnh", 1), ("Vàng miếng SJC giảm theo giá thế giới", 2)]


def feed(items):
    when = format_datetime(datetime.fromtimestamp(NOW - 600, timezone.utc))
    body = "".join(
        f"<item><title>{t}</title><link>https://vneconomy.vn/vang-{n}.htm</link><description>{t}</description>"
        f"<pubDate>{when}</pubDate></item>"
        for t, n in items
    )
    return {"vneconomy_tc": f"<rss version='2.0'><channel>{body}</channel></rss>"}


@pytest.fixture
def two_sides(tmp_path, monkeypatch):
    """TCB in inbox mode, the zone's address and both keys set; the zone's state file beside TCB's."""
    monkeypatch.setenv("MF_INBOX_KEY", INBOX_KEY)
    monkeypatch.setenv("MF_ZONE_KEY", ZONE_KEY)
    monkeypatch.setenv("MF_ZONE_URL", "http://zone")
    monkeypatch.setenv("MF_TCB_INBOX", "http://tcb/api/inbox")
    v = config.propose("ai_mode", {"mode": "inbox"}, "admin")
    config.decide(v["id"], "approve", "admin")
    return tmp_path / "zone.db"


@contextmanager
def zone(path):
    old = os.environ["MF_STATE"]
    os.environ.update(MF_STATE=str(path), MF_ZONE="on")
    try:
        yield
    finally:
        os.environ["MF_STATE"] = old
        os.environ.pop("MF_ZONE", None)


def to_zone(path):
    """TCB's push, delivered to the zone's door as app/zone.py serves it."""

    def send(url, body, headers):
        assert url == "http://zone/api/zone/sync"
        with zone(path), TestClient(zone_web.app) as c:
            r = c.post("/api/zone/sync", content=body, headers={"content-type": "application/json", **headers})
        return r.status_code, r.json()

    return send


def to_tcb(path, seen=None):
    """The zone's push, delivered to TCB's door (outside the zone's state); ``seen`` collects what came back."""

    def send(url, body, headers):
        assert url == "http://tcb/api/inbox"
        old = {k: os.environ.pop(k) for k in ("MF_ZONE", "MF_STATE")}
        os.environ["MF_STATE"] = str(path)
        try:
            with TestClient(Application.find(".").asgi()) as c:
                r = c.post("/api/inbox", content=body, headers={"content-type": "application/json", **headers})
        finally:
            os.environ.update(old)
        if seen is not None:
            seen.append(r.json())
        return r.status_code, r.json()

    return send


def test_the_round_trip_tcb_to_the_zone_and_back_through_the_inbox(two_sides, state):
    ok(INGEST, feeds=feed(GOLD), now=NOW)  # TCB fetches the feeds on its clock
    tcb_ids = [i["id"] for i in news_store.inbox()]

    sources = config.data("news_sources")
    sources[0]["outlet"] = sources[0]["outlet"] + " (đã duyệt lại)"
    config.decide(config.propose("news_sources", sources, "admin")["id"], "approve", "admin")
    news_store.add(
        [
            {
                "source": "research",
                "title": "Báo cáo vàng quý 4",
                "summary": "Vàng",
                "url": "research://RS-0001",
                "url_key": "research/RS-0001",
                "title_key": "research|bao cao vang quy 4",
                "ingested": NOW,
                "status": "new",
                "kind": "exclusive",
                "relevance": "low",
            }
        ]
    )

    out = sync.push(send=to_zone(two_sides))
    assert out["status"] == "ok", out["error"]
    assert out["applied"] == ["CF-news_sources-v2"] and out["research_added"] == 1
    assert sync.push(send=to_zone(two_sides))["status"] == "unchanged"  # sent again only when it changed

    seen = []
    with zone(two_sides):
        assert config.active("news_sources")["mirrored_from"] == "CF-news_sources-v2"  # TCB's approved list
        ok(INGEST, feeds=feed(GOLD), now=NOW)  # the zone fetches the same public feeds itself
        got = asyncio.run(agent.tick(now=NOW, send=to_tcb(state, seen)))
        made = got["made"]
        assert made["status"] == "sent" and made["tcb_id"].startswith("IN-")
        assert seen == [{"id": made["tcb_id"]}]  # the zone reads back an id, nothing else
        with db.tx() as con:  # no people, no clients, in the zone's file (ZONE-01)
            tables = {r[0] for r in con.execute("select name from sqlite_master where type = 'table'")}
        assert "people" not in tables and "client_sources" not in tables
        with pytest.raises(OutsideTheZone):
            people.staff()

    [done] = importer.run_ready()
    assert done["status"] == "IMPORTED", done
    v = vstore.get(done["view_id"])
    assert v["status"] == "PENDING_APPROVAL" and v["mode"] == "inbox"
    assert set(v["current"]["impacts"][0]["source_ids"]) <= set(tcb_ids)  # TCB's own news ids
    assert vstore.runs(v["id"])[0]["nodes"]  # the zone's trace, kept with the view


def test_the_zone_takes_one_event_a_tick_under_the_days_cap(two_sides, state, monkeypatch):
    monkeypatch.setenv("MF_ZONE_DAILY", "1")
    with zone(two_sides):
        ok(INGEST, feeds=feed(GOLD), now=NOW)
        assert asyncio.run(agent.tick(now=NOW, send=lambda *a: (202, {"id": "IN-000009"})))["made"]["status"] == "sent"
        ok(INGEST, feeds=feed([("Giá vàng thế giới tăng trở lại", 3)]), now=NOW)
        assert "Đã đủ 1" in asyncio.run(agent.tick(now=NOW))["reason"]


def test_a_package_tcb_does_not_take_is_sent_again_and_dropped_after_a_day(two_sides):
    answers = iter([(409, {"error": "Không ở chế độ hộp chờ"}), (202, {"id": "IN-000001"})])
    with zone(two_sides):
        ok(INGEST, feeds=feed(GOLD), now=NOW)
        made = asyncio.run(agent.tick(now=NOW, send=lambda *a: next(answers)))["made"]
        assert made["status"] == "waiting" and "hộp chờ" in made["last_error"]
        assert asyncio.run(agent.tick(now=NOW, send=lambda *a: next(answers)))["resent"] == ["sent"]
        oid = agent._add("EV-x", {"package": "{}", "attempts": 3}, "waiting")
        with db.tx() as con:
            con.execute("update zone_outbox set created = ? where id = ?", (time.time() - agent.GIVE_UP_S - 1, oid))
        assert agent.deliver(oid, send=lambda *a: (500, {}))["status"] == "failed"


def test_the_zones_door_takes_only_a_signed_bundle_of_the_catalogues(two_sides, monkeypatch):
    body = json.dumps(sync.bundle()).encode()
    with zone(two_sides):
        assert mirror.receive(body, None)[0] == 401
        assert mirror.receive(body, sign.sign(body + b" ", ZONE_KEY.encode()))[0] == 401
        bad = json.dumps({"version": 1, "catalogues": {"rm_assignment": {"id": "CF-rm_assignment-v1", "data": {}}}})
        code, reply = mirror.receive(bad.encode(), sign.sign(bad.encode(), ZONE_KEY.encode()))
        assert code == 400 and "rm_assignment" in reply["error"]  # who serves which family never goes
        assert mirror.receive(body, sign.sign(body, ZONE_KEY.encode())) == (200, {"applied": [], "research_added": 0})
    b = sync.bundle()
    assert set(b["catalogues"]) | set(b["not_set"]) == set(sync.KINDS) and b["not_set"] == ["models"]


def test_only_the_zone_mirrors_a_catalogue_and_only_the_zone_has_its_actor(two_sides):
    with pytest.raises(roles.Forbidden):
        config.mirror("restricted", config.data("restricted"), "CF-restricted-v1")
    with pytest.raises(roles.Forbidden):
        roles.require(roles.ZONE_ACTOR, "cio")
    monkeypatch_free = sync.push(send=lambda *a: (_ for _ in ()).throw(OSError("không tới được vùng AI")))
    assert monkeypatch_free["status"] == "failed" and "không tới được" in monkeypatch_free["error"]
    v = config.propose("ai_mode", {"mode": "live"}, "admin")
    config.decide(v["id"], "approve", "admin")
    assert sync.push()["status"] == "skipped"  # nothing goes to the zone outside inbox mode

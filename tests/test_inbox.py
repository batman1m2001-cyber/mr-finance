"""The signed inbox (BRD-RULE-ZONE-02/03, LC-04, SEC-07, FR-307 inbox mode; BRD completion F6): the AI zone writes
packages and reads nothing; the import takes each through the checks a live run passes, and imports it or
rejects it with the error, changing nothing."""

import json
import time

import pytest
from operonx.app import Application
from starlette.testclient import TestClient
from test_views import news, valid_view

from control import config, db
from inbox import importer, sign, store
from news import store as news_store
from views import store as vstore

KEY = "khoa-hop-cho-thu"


@pytest.fixture
def inbox_mode(monkeypatch):
    monkeypatch.setenv("MF_INBOX_KEY", KEY)
    v = config.propose("ai_mode", {"mode": "inbox"}, "admin")
    config.decide(v["id"], "approve", "admin")
    with TestClient(Application.find(".").asgi()) as c:
        yield c


def package(ids, **over):
    items = news_store.get(ids)
    refs = {i["id"]: f"Z{k + 1}" for k, i in enumerate(items)}
    view = json.loads(json.dumps(valid_view(ids)).replace('"' + ids[0] + '"', '"' + refs[ids[0]] + '"'))
    pkg = {
        "version": 1,
        "zone_run": "ZR-000001",
        "created": time.time(),
        "event": {"title": "Giá vàng thế giới giảm mạnh", "type": "commodity"},
        "news": [{"ref": refs[i["id"]], "url": i["url"], "title": i["title"], "source": i["source"]} for i in items],
        "view": view,
        "challenge": {
            "findings": [{"severity": "critical", "title": "Thiếu kịch bản vàng tăng lại", "source": "model"}]
        },
        "run": {
            "mode": "live",
            "models": {"cio": "vendor/big", "challenger": "other/small"},
            "prompt_version": "CF-prompts-v1",
            "nodes": [{"node": "synthesize", "mode": "live", "model": "vendor/big", "output": {"ok": True}}],
        },
    }
    pkg.update(over)
    return json.dumps(pkg, ensure_ascii=False).encode()


def push(c, body, signed=True):
    headers = {sign.HEADER: sign.sign(body, KEY.encode())} if signed else {}
    return c.post("/api/inbox", content=body, headers={"content-type": "application/json", **headers})


def test_a_signed_package_is_imported_as_a_view_waiting_for_the_cio(inbox_mode):
    ids = news("Giá vàng thế giới giảm mạnh", "Vàng miếng SJC giảm theo")
    r = push(inbox_mode, package(ids))
    assert r.status_code == 202 and set(r.json()) == {"id"}  # the zone reads nothing back
    assert store.get(r.json()["id"])["status"] == "READY"
    [done] = importer.run_ready()
    assert done["status"] == "IMPORTED", done
    v = vstore.get(done["view_id"])
    assert v["status"] == "PENDING_APPROVAL" and v["mode"] == "inbox" and v["event_id"] == done["event_id"]
    assert v["current"]["impacts"][0]["source_ids"] == ids[:1]  # the zone's reference became TCB's news id
    [cio_run, ch_run] = vstore.runs(v["id"])
    assert cio_run["mode"] == "inbox" and cio_run["nodes"][0]["zone_mode"] == "live"
    findings = vstore.challenges(v["id"])[-1]["findings"]
    assert any(f["source"] == "zone" and f["title"].startswith("Thiếu kịch bản") for f in findings)
    assert store.get(r.json()["id"])["status"] == "IMPORTED"
    with db.tx() as con:
        assert con.execute("select count(*) from audit_log where action = 'inbox.imported'").fetchone()[0] == 1


@pytest.mark.parametrize(
    "spoil, error",
    [
        (lambda ids: {"version": 2}, "version 1"),
        (lambda ids: {"news": [{"ref": "Z1", "url": "https://evil.example/x", "source": "evil"}]}, "danh sách trắng"),
        (lambda ids: {"challenge": {"findings": [{"severity": "huge", "title": "x"}]}}, "severity"),
        (lambda ids: {"run": {"mode": "magic", "models": {}}}, "run.mode"),
    ],
)
def test_a_package_that_fails_a_check_is_rejected_with_why_and_changes_nothing(inbox_mode, spoil, error):
    ids = news("Giá vàng thế giới giảm mạnh", "Vàng miếng SJC giảm theo")
    before = len(vstore.runs("x")), len(news_store.get(ids))
    pid = push(inbox_mode, package(ids, **spoil(ids))).json()["id"]
    [done] = importer.run_ready()
    assert done["status"] == "REJECTED" and error in done["error"]
    assert store.get(pid)["status"] == "REJECTED"
    assert all(i["status"] == "new" for i in news_store.get(ids))  # no event was made
    assert before == (len(vstore.runs("x")), len(news_store.get(ids)))


def test_a_view_whose_sources_are_not_the_events_news_is_rejected(inbox_mode):
    ids = news("Giá vàng thế giới giảm mạnh", "Vàng miếng SJC giảm theo")
    body = package(ids).replace(b'"source_ids": ["Z1"]', b'"source_ids": ["Z9"]', 1)
    push(inbox_mode, body)
    [done] = importer.run_ready()
    assert done["status"] == "REJECTED" and "không thuộc sự kiện" in done["error"]


def test_unsigned_or_wrongly_signed_is_rejected_when_the_key_is_set(inbox_mode):
    ids = news("Giá vàng thế giới giảm mạnh")
    push(inbox_mode, package(ids), signed=False)
    bad = package(ids)
    inbox_mode.post("/api/inbox", content=bad, headers={sign.HEADER: sign.sign(bad + b" ", KEY.encode())})
    assert [d["status"] for d in importer.run_ready()] == ["REJECTED", "REJECTED"]
    assert all("chữ ký" in r["error"] for r in store.recent())


def test_news_tcb_has_not_fetched_waits_then_is_rejected_after_an_hour(inbox_mode):
    ids = news("Giá vàng thế giới giảm mạnh")
    body = json.loads(package(ids))
    body["news"][0]["url"] = "https://vneconomy.vn/chua-co.htm"
    pid = push(inbox_mode, json.dumps(body).encode()).json()["id"]
    assert importer.run_ready()[0]["status"] == "READY"
    with db.tx() as con:
        con.execute("update external_outputs set received = ? where id = ?", (time.time() - 3700, pid))
    assert importer.run_ready()[0]["status"] == "REJECTED"


def test_restricted_news_is_rejected_for_the_cio(inbox_mode):
    ids = news("Sao Mai Land chậm trả lãi trái phiếu, tín dụng bất động sản căng")
    push(inbox_mode, package(ids))
    [done] = importer.run_ready()
    assert done["status"] == "REJECTED" and "danh sách hạn chế" in done["error"]


def test_the_door_opens_only_in_inbox_mode_and_refuses_floods(inbox_mode, monkeypatch):
    v = config.propose("ai_mode", {"mode": "live"}, "admin")
    config.decide(v["id"], "approve", "admin")
    assert push(inbox_mode, b"{}").status_code == 409
    v = config.propose("ai_mode", {"mode": "inbox"}, "admin")
    config.decide(v["id"], "approve", "admin")
    assert push(inbox_mode, b"x" * (store.MAX_BYTES + 1)).status_code == 413
    monkeypatch.setattr(store, "MAX_WAITING", 1)
    assert push(inbox_mode, b"{}").status_code == 202
    assert push(inbox_mode, b"{}").status_code == 429

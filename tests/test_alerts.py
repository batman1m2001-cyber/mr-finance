"""Alerts and the central log (BRD-NFR-12), and an AI outage (BRD-NFR-03; BRD completion F7): what fails raises one
alert for the people who look after it, counts up while it keeps failing and resolves when it works again;
acknowledging is audited; and with the model provider unreachable the engine, the runs and the reads still work."""

import asyncio
import json
from datetime import date
from types import SimpleNamespace

import pytest
from operonx.app import Application
from starlette.testclient import TestClient
from test_views import GOLD, INGEST, NOW, agent, decide, event, ok

from control import alerts, db, log, roles
from market import fetch
from views import queue, worker
from views import store as vstore


def feeds(xml):
    return {"vneconomy_tc": xml}


GOOD = "<rss version='2.0'><channel><item><title>Lãi suất ổn định</title><link>https://vneconomy.vn/a.htm</link></item></channel></rss>"


def test_a_feed_that_fails_raises_one_alert_counts_up_and_resolves_when_it_answers():
    ok(INGEST, feeds=feeds("<rss><không phải xml"), now=NOW)
    ok(INGEST, feeds=feeds("<rss><không phải xml"), now=NOW)
    [a] = alerts.for_role("cio")
    assert (a["kind"], a["key"], a["status"], a["count"]) == ("news_feed", "vneconomy_tc", "open", 2)
    assert alerts.for_role("rm") == []  # each role its kinds
    ok(INGEST, feeds=feeds(GOOD), now=NOW)
    assert alerts.for_role("cio") == [] and alerts.recent()[0]["status"] == "resolved"
    events = [x["event"] for x in log.recent(10)]
    assert events[:2] == ["alert.resolve", "alert.raise"]  # the central log, newest first


def test_a_market_series_no_source_answers_raises_an_alert():
    def down(*a, **k):
        raise OSError("mất kết nối")

    out = fetch.run_job("market_crypto", down, today=date(2026, 9, 10))
    assert out["errors"] and {a["kind"] for a in alerts.for_role("admin")} == {"market_job"}
    assert {a["key"] for a in alerts.for_role("cio")} == {s["series"] for s in out["series"]}


def test_a_broken_audit_chain_alerts_the_cio_and_admin_and_resolves_when_whole():
    event(*GOLD)  # a few audit rows
    run = _chain_check
    assert run()["ok"] and alerts.for_role("cio") == []
    with db.tx() as con:
        con.execute("drop trigger audit_log_no_update")  # someone with the database file edits a row
        con.execute("update audit_log set actor = 'ai-đó' where seq = 1")
    assert not run()["ok"]
    got = alerts.for_role("cio")
    assert {a["key"] for a in got} == {"chain", "worm"}  # the chain, and the write-once segment holding row 1
    assert all(a["kind"] == "audit_chain" and a["severity"] == "high" for a in got) and alerts.for_role("rm") == []


def _chain_check():
    from operonx import Operon

    from control.graph import audit_check_flow

    return asyncio.run(Operon(audit_check_flow, params={"tick": None, "at": None}).run(inputs={}))["chain"]


def test_acknowledging_is_for_the_roles_it_is_for_and_is_audited():
    a = alerts.raise_("agent", "cio", "Agent cio lỗi (thử)", "thử")
    with pytest.raises(roles.Forbidden):
        alerts.ack(a["id"], "rm01")
    done = alerts.ack(a["id"], "cio", "Đã báo nhà cung cấp")
    assert done["status"] == "acked" and done["history"][-1]["by"] == "cio"
    with pytest.raises(ValueError, match="acked"):
        alerts.ack(a["id"], "admin")
    assert alerts.raise_("agent", "cio", "Agent cio lỗi (thử)")["count"] == 2  # still the same one
    with db.tx() as con:
        acts = [r[0] for r in con.execute("select action from audit_log where object = ?", (a["id"],))]
    assert acts == ["alert.raise", "alert.ack"]
    with TestClient(Application.find(".").asgi()) as c:
        r = c.post("/api/system/alerts/ack", json={"alert_id": a["id"], "by": "admin"})
        assert r.status_code == 409  # already acknowledged
        assert c.get("/api/system/alerts?role=cio").json()["alerts"][0]["status"] == "acked"
        d = c.get("/api/system").json()
        assert d["alerts"][0]["id"] == a["id"] and d["log"][0]["event"] == "alert.raise"


@pytest.fixture
def provider_down(monkeypatch):
    """Live mode with both models set, and the provider's address one where nothing listens: a real refused
    connection, not a fake reply."""
    from operonx.providers.llms.factory import create_llm
    from operonx.providers.ops import _utils as hub_utils

    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_CIO", "vendor/big-model")
    monkeypatch.setenv("LLM_MODEL_CHALLENGER", "vendor/small-model")
    real = hub_utils.resolve_hub()
    dead = {}
    for key, model in (("llm:cio", "vendor/big-model"), ("llm:challenger", "vendor/small-model")):
        cfg = real.get(key).config.model_copy(
            update={"base_url": "http://127.0.0.1:9/v1", "model": model, "max_retries": 0, "retry": None, "timeout": 5}
        )
        dead[key] = create_llm(cfg)
    monkeypatch.setattr(hub_utils, "resolve_hub", lambda: SimpleNamespace(get=lambda key: dead[key]))


def test_with_the_ai_provider_down_computing_runs_and_reads_still_work(provider_down, monkeypatch):
    # an approved view and its application run, from before the outage (mock mode)
    monkeypatch.setenv("MF_AI", "off")
    ev = event(*GOLD)
    v = agent(ev["id"])["view"]
    run = decide(v["id"], "approve")["decision"]["run"]
    monkeypatch.setenv("MF_AI", "on")

    # the outage: the agent run fails with why, nothing is stuck, an alert is raised for the CIO
    ev2 = event("Lãi suất liên ngân hàng tăng", "NHNN hút ròng qua tín phiếu")
    job = queue.enqueue(ev2["id"], "cio")
    assert job["mode"] == "live"
    done = asyncio.run(worker.run_next())
    view = vstore.get(done["view_id"])
    assert view["status"] == "AGENT_ERROR" and "Không gọi được mô hình" in json.dumps(view["error"], ensure_ascii=False)
    assert all(r["status"] != "running" for r in vstore.runs(view["id"]))
    assert any(a["kind"] == "agent" for a in alerts.for_role("cio"))

    # computing and reading do not need the model
    with TestClient(Application.find(".").asgi()) as c:
        assert c.post("/api/dashboard", json={"client_id": "C01"}).status_code == 200
        assert c.get("/api/families/C01/impact").status_code == 200
        assert c.get(f"/api/runs/{run['id']}").status_code == 200
        again = c.post("/api/runs/recompute", json={"run": run["id"], "by": "cio"})
        assert again.status_code == 200, again.text
        assert c.post("/api/alerts", json={"client_id": "C01"}).status_code == 200

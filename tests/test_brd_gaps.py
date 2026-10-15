"""Small BRD gaps closed on 2026-10-16: audit export (FR-702), health protections (RULE-SEC-10), token budget
and cost per event (NFR-10), client sources without headlines (RULE-CONTENT-02)."""

import csv
import io

import pytest
from starlette.testclient import TestClient
from test_apply import MARKET, approved

from apply import reads
from control import audit, db
from views import agents
from views import store as vstore


def client():
    from app.web import app

    return TestClient(app)


def test_the_audit_export_is_the_whole_chain_and_reverifies():
    approved(*MARKET)
    out = client().get("/api/audit/export").json()
    assert out["verify"]["ok"] and len(out["rows"]) == out["verify"]["count"] > 0
    prev = out["genesis"]  # an auditor can walk the exported chain without the database
    for r in out["rows"]:
        assert r["prev_hash"] == prev
        prev = r["hash"]
    assert prev == out["verify"]["head"]
    raw = client().get("/api/audit/export?format=csv")
    assert raw.headers["content-disposition"].startswith("attachment") and raw.headers["content-type"].startswith(
        "text/csv"
    )
    rows = list(csv.DictReader(io.StringIO(raw.text)))
    assert [int(r["seq"]) for r in rows] == [r["seq"] for r in out["rows"]]


def test_health_lists_the_protections_that_are_off(monkeypatch):
    monkeypatch.delenv("AUDIT_HMAC_KEY", raising=False)
    h = client().get("/healthz").json()
    assert h["ok"] and {"audit_hmac", "two_models", "sign_in"} <= set(h["off"])
    monkeypatch.setenv("AUDIT_HMAC_KEY", "k" * 32)
    assert "audit_hmac" not in client().get("/healthz").json()["off"]


def test_the_daily_token_budget_stops_a_live_call_and_cost_is_kept_per_event(monkeypatch):
    rid = vstore.start_run("cio", "EV-TEST", "live", "m1")
    vstore.add_node(rid, {"node": "analyst", "tokens_in": 900, "tokens_out": 300})
    assert vstore.tokens()["by_subject"]["EV-TEST"] == 1200
    monkeypatch.setenv("AGENT_DAILY_TOKENS", "2000")
    assert agents.budget() == {"daily": 2000, "used_today": 1200}
    with pytest.raises(agents.AgentError, match="ngân sách"):
        import asyncio

        asyncio.run(agents.call_model("cio", "s", "u", agents.MAX_TOKENS["analyst"]))  # 1200 + 3000 > 2000


def test_the_client_sees_outlets_not_headlines():
    _, run = approved(*MARKET)
    item = next(i for i in reads.family_impact("C01", "client")["items"] if i["run_id"] == run["id"])
    assert item["sources"]["count"] >= 1 and item["sources"]["outlets"] == ["VnEconomy"]
    with db.tx() as con:
        assert audit.verify(con)["ok"]

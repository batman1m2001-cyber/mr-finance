"""FR-703 agent catalogue and RULE-MEAS-04 AI quality (src/views/catalogue.py)."""

from starlette.testclient import TestClient
from test_apply import MARKET, approved

from views import catalogue


def test_one_entry_per_agent_with_the_six_fields():
    out = catalogue.catalogue()
    ids = [a["id"] for a in out["agents"]]
    assert ids[:4] == ["cio", "challenger", "policy", "explain"]  # the BRD §8 table, in its order
    for a in out["agents"]:
        assert all(a[k] for k in ("purpose", "owner", "risk", "brd_model", "model", "mode"))
    assert {r["name"] for r in out["references"]} >= {"TradingAgents", "FinRobot"}
    policy = next(a for a in out["agents"] if a["id"] == "policy")
    assert policy["built"] is False and policy["mode"] == "not_built"


def test_the_latest_run_and_the_quality_figures_come_from_the_store():
    assert catalogue.catalogue()["agents"][0]["latest_run"] is None
    approved(*MARKET)  # mock agent + challenger, then the CIO approves
    cio = catalogue.catalogue()["agents"][0]
    assert cio["latest_run"]["mode"] == "mock" and cio["latest_run"]["status"] == "ok"
    q = catalogue.quality()
    assert q["recent"]["decided"] == 1 and q["recent"]["edited_share"] == 0.0
    assert q["recent"]["agent_runs"] >= 1 and q["recent"]["failed_runs"] == 0
    assert q["all_time"]["views"] >= q["recent"]["views"]


def test_the_endpoint():
    from app.web import app

    c = TestClient(app)
    body = c.get("/api/agents/catalogue?days=30").json()
    assert body["quality"]["days"] == 30 and len(body["agents"]) == 5
    assert c.get("/api/agents/catalogue?days=x").status_code == 400

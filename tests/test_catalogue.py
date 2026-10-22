"""FR-703 agent catalogue and RULE-MEAS-04 AI quality (src/views/catalogue.py)."""

import re
from pathlib import Path

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
    assert policy["built"] is True and policy["mode"] == "mock" and policy["resource"] == "llm:cio"  # F9


SRC = Path(__file__).resolve().parent.parent / "src"
# A model call through a setting: Model("copilot"), agents.call_model(...), hub.get("llm:..."), resource=mode[...]
CALLS = re.compile(r'Model\("|call_model\(|\.get\(f?"llm:|resource=mode')
ONLY_NAMES = {"control/barrier.py", "views/catalogue.py"}  # the barrier classifies settings; the checklist lists them


def test_every_model_call_belongs_to_a_checklist_entry():
    """AGENT_CHECKLIST_PLAN C2: a new model call without a line in the checklist fails here."""
    listed = {f for e in catalogue.ENTRIES for f in e.get("code", [])}
    calling = {
        str(p.relative_to(SRC.parent))
        for p in SRC.rglob("*.py")
        if str(p.relative_to(SRC)) not in ONLY_NAMES and CALLS.search(p.read_text())
    }
    assert calling, "the pattern found no model call: it no longer matches the code"
    assert calling <= listed, f"calls a model but is in no checklist entry: {sorted(calling - listed)}"
    for f in listed:
        assert (SRC.parent / f).is_file(), f"checklist names a file that is gone: {f}"


def test_every_entry_has_a_name_an_owner_and_a_measure():
    evals = {e["id"] for e in catalogue.EVALUATIONS}
    ids = [e["id"] for e in catalogue.ENTRIES]
    assert len(ids) == len(set(ids)) == 8
    names = [e["name"] for e in catalogue.ENTRIES]
    assert len(names) == len(set(names))
    for e in catalogue.ENTRIES:
        assert e["name"] and e["owner"] and e["owner_roles"] and e["purpose"]
        assert set(e["measured"]) <= evals  # [] means "chưa đo", said plainly on the page
    out = catalogue.catalogue()
    assert [e["id"] for e in out["evaluations"]] == ["daily_trial", "change_gate", "assistant_set"]
    for e in out["evaluations"]:
        assert e["agents"] and "latest" in e
    copilot = next(a for a in out["agents"] if a["id"] == "copilot")
    assert copilot["resource"] == "llm:copilot" and copilot["measured"] == ["assistant_set"]


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
    assert body["quality"]["days"] == 30 and len(body["agents"]) == 8 and len(body["evaluations"]) == 3
    assert c.get("/api/agents/catalogue?days=x").status_code == 400

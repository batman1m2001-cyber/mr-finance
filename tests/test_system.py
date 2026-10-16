"""Hệ thống, the Admin's screen (BRD-RULE-ROLE-04, NFR-12; BRD completion F5): the jobs and how each last went,
the feeds, the agents, the audit chain, the people; and a load of the market history an Admin asks for, run by
the ``market_load`` job."""

import asyncio

import pytest
from operonx.app import Application
from starlette.testclient import TestClient

from control import audit, db
from market import fetch, ops, store
from people import auth


@pytest.fixture
def admin(monkeypatch):
    monkeypatch.setenv("MF_AUTH", "on")
    with TestClient(Application.find(".").asgi()) as c:
        c.cookies.set(auth.COOKIE, auth.issue("admin"))
        yield c


def test_the_system_read_lists_the_jobs_the_chain_and_the_people(admin):
    d = admin.get("/api/system").json()
    jobs = {j["id"]: j for j in d["jobs"]}
    assert {"news_ingest", "market_fx", "market_load", "agent_eval", "accuracy_score", "market_backfill"} <= set(jobs)
    assert jobs["market_load"]["when"] == {"every": "1m"} and jobs["market_backfill"]["when"] == {}
    assert d["chain"]["ok"] is True
    people = {p["id"]: p for p in d["people"]}
    assert people["rm01"]["families"] == ["C01", "C04", "C05"] and people["admin2"]["role"] == "admin"
    assert "C01" not in people and d["clients"] >= 5
    assert {c["kind"] for c in d["config_waiting"]} == set()


def test_an_admin_asks_for_a_load_and_the_job_runs_it(admin, monkeypatch):
    calls = []

    def run_job(job, *_args):
        calls.append((job, _args[2].isoformat()))
        return {"job": job, "series": [], "points": 3, "errors": 0}

    monkeypatch.setattr(fetch, "run_job", run_job)
    r = admin.post("/api/market/load", json={"by": "admin", "since": "2026-01-01"})
    assert r.status_code == 200 and r.json()["load"]["queued"] is True
    again = admin.post("/api/market/load", json={"by": "admin", "since": "2025-01-01"}).json()["load"]
    assert again["queued"] is False and again["since"] == "2026-01-01"  # one at a time
    assert admin.post("/api/market/load", json={"by": "admin", "since": "2001-01-01"}).status_code == 400
    assert admin.post("/api/market/load", json={"by": "admin", "since": "hôm qua"}).status_code == 400
    with db.tx() as con:
        assert any(r["action"] == "market.load_asked" for r in audit.export(con)["rows"])
    out = asyncio.run(ops.load_pending())
    assert out["status"] == "done" and out["points"] == 3 * len(fetch.jobs())
    assert {c[1] for c in calls} == {"2026-01-01"} and len(calls) == len(fetch.jobs())
    assert asyncio.run(ops.load_pending()) is None  # nothing waits
    last = admin.get("/api/system").json()
    assert next(j for j in last["jobs"] if j["id"] == "market_load")["last"]["ok"] is True


def test_a_load_that_keeps_nothing_is_failed_and_says_why(monkeypatch):
    monkeypatch.setattr(fetch, "run_job", lambda job, *a: {"job": job, "series": [], "points": 0, "errors": 2})
    store.request_load("admin", "2026-01-01")
    out = asyncio.run(ops.load_pending())
    assert out["status"] == "failed" and "không lấy được" in out["error"]

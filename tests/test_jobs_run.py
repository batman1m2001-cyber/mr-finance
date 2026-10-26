"""Việc nền (owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md A): Admin runs a background job now, one at a time,
recorded and audited; a failed run raises the job alert; the page's read shows the agents' queue, what the CIO may
start and the jobs; the assistant's agent_nen says, per role, what can be run."""

import asyncio
import time

import pytest
from starlette.testclient import TestClient

from assistant import desktools
from assistant.base import Ctx
from control import alerts, audit, db, jobs, roles
from control.errors import Conflict


class Rec:
    def __init__(self, errors=None):
        self.run_id, self.items, self.timed_out = "R-1", [object(), object()], []
        self.errors = errors or {}
        self.failed = [object()] if errors else []


class FakeJob:
    def __init__(self, name, errors=None, boom=None):
        self.name, self.errors, self.boom, self.calls = name, errors, boom, []

    async def run(self, **kw):
        self.calls.append(kw)
        if self.boom:
            raise self.boom
        return Rec(self.errors)


@pytest.fixture
def job(state, monkeypatch):
    j = FakeJob("audit_check")
    monkeypatch.setitem(jobs._JOBS, "audit_check", j)
    return j


def test_admin_runs_a_job_now_and_it_is_recorded_and_audited(job):
    async def go():
        row = jobs.run_now("audit_check", "admin")
        assert row["status"] == "running" and row["by"] == "admin" and row["label"] == "Kiểm tra chuỗi nhật ký"
        await jobs.settle()
        return jobs.get(row["id"])

    done = asyncio.run(go())
    assert done["status"] == "done" and done["summary"] == {"items": 2, "failed": 0, "record": "R-1"}
    assert job.calls == [{"trigger": {"by": "admin", "manual": done["id"]}}]
    with db.tx() as con:
        acts = [r["action"] for r in con.execute("select action from audit_log where object = ?", (done["id"],))]
        assert acts == ["job.run_now", "job.run_done"] and audit.verify(con)["ok"]


def test_a_failed_or_crashed_run_is_failed_and_raises_the_job_alert(state, monkeypatch):
    monkeypatch.setitem(jobs._JOBS, "news_ingest", FakeJob("news_ingest", errors={"vneconomy": "HTTP 503"}))
    monkeypatch.setitem(jobs._JOBS, "market_fx", FakeJob("market_fx", boom=RuntimeError("không kết nối")))

    async def go():
        a = jobs.run_now("news_ingest", "admin")
        b = jobs.run_now("market_fx", "admin")
        await jobs.settle()
        return jobs.get(a["id"]), jobs.get(b["id"])

    a, b = asyncio.run(go())
    assert a["status"] == "failed" and "HTTP 503" in a["error"]
    assert b["status"] == "failed" and b["error"] == "RuntimeError: không kết nối"
    opened = {x["key"] for x in alerts.for_role("admin") if x["kind"] == "job"}
    assert opened == {"news_ingest", "market_fx"}
    assert not [x for x in alerts.for_role("cio") if x["kind"] == "job"]  # Admin's alert


def test_one_run_at_a_time_and_a_stale_one_is_failed(job):
    first = jobs.start("audit_check", "admin")
    with pytest.raises(Conflict, match="đang chạy"):
        jobs.start("audit_check", "admin")
    with db.tx() as con:  # the server stopped mid-run, 31 minutes ago
        con.execute("update job_runs set created = ? where id = ?", (time.time() - 31 * 60, first["id"]))
    again = jobs.start("audit_check", "admin")
    assert jobs.get(first["id"])["status"] == "failed" and again["status"] == "running"


@pytest.mark.parametrize("name", ["heartbeat", "agent_worker", "market_load", "assistant_retention", "nope"])
def test_the_clockwork_and_unknown_jobs_are_not_run_by_hand(job, name):
    with pytest.raises(ValueError, match="không chạy tay được"):
        jobs.start(name, "admin")


@pytest.mark.parametrize("who", ["cio", "rm01"])
def test_only_admin_runs_a_job(job, who):
    with pytest.raises(roles.Forbidden):
        jobs.start("audit_check", who)


def _client():
    from app.web import app

    return TestClient(app)


def test_the_page_read_shows_agents_jobs_and_manual_runs(job, monkeypatch):
    from app import web

    monkeypatch.setattr(web, "JOBS", [{"id": "audit_check", "description": "", "when": {"every": "1h"}},
                                      {"id": "heartbeat", "description": "", "when": {"every": "20s"}}])  # fmt: skip
    jobs.start("audit_check", "admin")
    d = _client().get("/api/jobs").json()
    assert set(d) == {"agents", "jobs", "manual"}
    assert set(d["agents"]) == {"status", "health", "queue", "can_run", "can_challenge"}
    by = {j["id"]: j for j in d["jobs"]}
    assert by["audit_check"]["runnable"] and by["audit_check"]["running"] == d["manual"][0]["id"]
    assert not by["heartbeat"]["runnable"] and by["heartbeat"]["running"] is None
    assert web.allowed_roles("/api/jobs") == ("cio", "admin")


def test_what_the_cio_may_start_and_agent_nen_says_it(state, monkeypatch):
    from test_assistant_tools import rss

    from assistant import base
    from events.graph import event_flow
    from news.graph import ingest_flow

    monkeypatch.setattr("news.ops._get", lambda url, timeout: rss(url, "Giá vàng SJC giảm mạnh"))
    ids = asyncio.run(base.run_graph(ingest_flow, feeds=None, now=None, tick=None, at=None))["ingest"]["ids"]
    ev = asyncio.run(base.run_graph(event_flow, news_ids=ids, title=None, by="cio"))["event"]
    from app.web import agents_read

    assert [e["id"] for e in agents_read()["can_run"]] == [ev["id"]]
    said = {r: asyncio.run(desktools.background(Ctx(r, None, "personal", "", user=r), {}))["text"] for r in
            ("cio", "admin")}  # fmt: skip
    assert ev["id"] in said["cio"] and "Xác nhận" in said["cio"] and "không chạy agent" not in said["cio"]
    assert "Kiểm tra chuỗi nhật ký" in said["admin"] and "CIO" in said["admin"]

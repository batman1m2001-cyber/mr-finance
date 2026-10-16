"""The agent run queue and the run modes (BRD-RULE-AI-13, BRD-FR-307; BRD completion F6): “Chạy Agent CIO” queues
a job and answers at once; the ``agent_worker`` job runs it through the same graph; the event page reads the job.
Admin sets the mode: live, inbox (nothing runs here) or mock."""

import asyncio
import time

import pytest
from operonx.app import Application
from starlette.testclient import TestClient
from test_views import GOLD, event

from control import config, db, roles
from control.errors import Conflict
from views import queue, worker
from views import store as vstore


def _admin_sets(mode):
    v = config.propose("ai_mode", {"mode": mode}, "admin")
    config.decide(v["id"], "approve", "admin")


def test_the_run_is_queued_and_answered_at_once():
    ev = event("Lãi suất liên ngân hàng tăng", "NHNN hút ròng qua tín phiếu")
    with TestClient(Application.find(".").asgi()) as c:
        t0 = time.time()
        r = c.post("/api/events/run-agent", json={"event_id": ev["id"], "by": "cio"})
        assert r.status_code == 200 and time.time() - t0 < 5
        job = r.json()["job"]
        assert job["status"] == "queued" and job["queued"] is True and job["mode"] == "mock"
        again = c.post("/api/events/run-agent", json={"event_id": ev["id"], "by": "cio"}).json()["job"]
        assert again["id"] == job["id"] and again["queued"] is False  # one open run per event
        assert c.get(f"/api/events/{ev['id']}").json()["jobs"][-1]["status"] == "queued"
        assert vstore.runs(ev["id"]) == [] and c.get(f"/api/events/{ev['id']}").json()["views"] == []

        done = asyncio.run(worker.run_next())  # the agent_worker job's tick
        assert done["status"] == "done" and done["view_id"].startswith("VW-")
        view = c.get(f"/api/views/{done['view_id']}").json()["view"]
        assert view["status"] == "PENDING_APPROVAL" and view["event_id"] == ev["id"]
        assert asyncio.run(worker.run_next()) is None  # nothing waits
        assert c.post("/api/events/run-agent", json={"event_id": ev["id"], "by": "cio"}).json()["job"]["queued"]


def test_who_and_which_event_are_checked_when_queued():
    with pytest.raises(roles.Forbidden):
        queue.enqueue(event(*GOLD)["id"], "rm01")
    held = event("Sao Mai Land chậm trả lãi trái phiếu, tín dụng bất động sản căng")  # restricted: held
    with pytest.raises(Conflict, match="bị giữ"):
        queue.enqueue(held["id"], "cio")


def test_a_run_that_fails_is_a_failed_job_with_why(monkeypatch):
    ev = event("Giá dầu Brent tăng", "OPEC cắt giảm sản lượng")
    job = queue.enqueue(ev["id"], "cio")
    from views import ops

    def boom(*a, **k):
        raise RuntimeError("mô hình không trả lời")

    monkeypatch.setattr(ops.agents, "synthesize", boom)
    out = asyncio.run(worker.run_next())
    assert out["id"] == job["id"] and out["status"] == "failed" and out["error"]


def test_a_run_left_running_by_a_dead_worker_is_failed_and_the_event_can_run_again():
    ev = event("Tỷ giá USD/VND tăng", "Ngân hàng nâng giá bán USD")
    job = queue.enqueue(ev["id"], "cio")
    queue.claim()
    with db.tx() as con:
        con.execute(
            "update agent_jobs set data = json_set(data, '$.started', ?) where id = ?",
            (time.time() - queue.STALE_S - 1, job["id"]),
        )
    assert queue.claim() is None
    assert queue.get(job["id"])["status"] == "failed"
    assert queue.enqueue(ev["id"], "cio")["queued"] is True


def test_admin_sets_the_mode_inbox_runs_nothing_here_mock_never_calls_a_model(monkeypatch):
    ev = event("Lạm phát tháng 9 tăng", "Giá xăng dầu tăng")
    _admin_sets("inbox")
    with pytest.raises(Conflict, match="hộp chờ"):
        queue.enqueue(ev["id"], "cio")
    from views import ops

    assert ops.agent_status()["mode"] == "inbox"
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_CIO", "a/one")
    monkeypatch.setenv("LLM_MODEL_CHALLENGER", "b/two")
    _admin_sets("mock")
    assert queue.enqueue(ev["id"], "cio")["mode"] == "mock"
    with pytest.raises(ValueError):
        config.propose("ai_mode", {"mode": "auto"}, "admin")
    with pytest.raises(roles.Forbidden):
        config.propose("ai_mode", {"mode": "live"}, "cio")

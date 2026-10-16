"""The Agent Ecosystem Map (A7, ADR-0033; OWN-AS-20…22): every edge is something the code does, every tool is on the
map, and each part's state is what its runs recorded — compared here with the traces of the same runs, made by the
real jobs into a folder of their own. The assistant's services keep no trace (a question is a person's words): the
map reads their turns from the audit log."""

import asyncio
import json
import os
from pathlib import Path

import pytest
from operonx import Operon
from operonx.app import Application
from starlette.testclient import TestClient
from test_assistant_agents import TALK, Model, talk
from test_views import GOLD, event

from assistant import registry
from assistant.graph import assistant_flow
from views import ecosystem, queue

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def traced(tmp_path, monkeypatch):
    """The jobs' run records and traces in this test's folder, read back by the map from the same place."""
    monkeypatch.setenv("OPERONX_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setattr("operonx.app.jobs.job.Job.records", lambda self: tmp_path / "jobs")
    ecosystem._FINISHED.clear()
    return tmp_path


def job(name):
    from app.main import APP

    return asyncio.run(APP.job(name).run())


def traces(name):
    """The traces of the job's last run: each item's meta.json (status, errors, output)."""
    root = Path(os.environ["OPERONX_RUNS_DIR"]) / "jobs" / name
    last = sorted(root.iterdir())[-1]
    return [json.loads((d / "meta.json").read_text("utf-8")) for d in last.iterdir() if (d / "meta.json").exists()]


def node(node_id):
    return next(n for n in ecosystem.ecosystem()["nodes"] if n["id"] == node_id)


STATE_OF_TRACE = {"ok": "done", "error": "failed"}


# -- the drawing is the code ---------------------------------------------------------------------------------------


def test_every_edge_names_code_that_exists_and_joins_two_nodes():
    ids = {n["id"] for n in ecosystem.NODES}
    assert [r for r in ecosystem.code_refs() if not ecosystem.holds(r)] == []
    assert all(e["from"] in ids and e["to"] in ids and e["from"] != e["to"] for e in ecosystem.EDGES)
    assert len({(e["from"], e["to"]) for e in ecosystem.EDGES}) == len(ecosystem.EDGES)  # one line per pair
    joined = {e["from"] for e in ecosystem.EDGES} | {e["to"] for e in ecosystem.EDGES}
    assert joined == ids  # nothing floats
    assert {n["group"] for n in ecosystem.NODES} == {g["id"] for g in ecosystem.GROUPS}
    assert all(set(f["nodes"]) <= ids for f in ecosystem.FLOW)
    assert not ecosystem.holds("src/views/ops.py::no_such_symbol")  # the check can fail


def test_every_part_wears_an_icon_the_kit_has():
    import re

    kit = set(re.findall(r"^  (\w+):", (ROOT / "web" / "core" / "icons.js").read_text("utf-8"), re.M))
    assert {n["icon"] for n in ecosystem.NODES} <= kit


def test_every_tool_of_the_assistant_is_on_the_map_once():
    tools = ecosystem._tools()
    names = [t["name"] for fam in tools.values() for t in fam]
    assert sorted(names) == sorted(registry.REGISTRY) and len(names) == len(set(names))
    m = {n["id"]: n for n in ecosystem.ecosystem()["nodes"]}
    assert sum(m[f]["tools"] for f in ecosystem.TOOL_FAMILIES) == len(registry.REGISTRY)
    assert m["tools_knowledge"]["kinds"]["paid"] == 1  # the web search, the one tool that costs


def test_the_assistant_services_keep_no_trace():
    described = {s["name"]: s for s in Application.load(ROOT / "operonx.toml").describe()["services"]}
    for name in ("assistant", "copilot", "assistant_conversations", "assistant_memory"):
        assert described[name]["sinks"] == [], name
    assert described["assistant_consolidate"]["sinks"] == ["local"]  # a job's trace holds counts, not text


# -- states from records, matched with traces ----------------------------------------------------------------------


def test_the_policy_sweep_state_matches_its_traces(traced, monkeypatch):
    assert node("policy_sweep")["state"] == "idle"
    assert job("policy_sweep").status == "ok"
    metas = traces("policy_sweep")
    assert metas and {m["status"] for m in metas} == {"ok"}
    assert node("policy_sweep")["state"] == "done"

    from wealth import fixtures

    real = fixtures.client

    def broken(cid):
        if cid == "C02":
            raise RuntimeError("nguồn hỏng")
        return real(cid)

    monkeypatch.setattr(fixtures, "client", broken)
    assert job("policy_sweep").status == "failed"
    metas = traces("policy_sweep")
    assert sorted(m["status"] for m in metas).count("error") == 1
    n = node("policy_sweep")
    assert n["state"] == "failed" and n["day"] == {"runs": 2, "failed": 1}

    rows = ecosystem.runs("policy_sweep")["runs"]
    assert [r["state"] for r in rows] == ["failed", "done"]  # newest first
    detail = ecosystem.run("policy_sweep", rows[0]["id"])
    bad = next(i for i in detail["items"] if i["state"] == "failed")
    assert bad["key"] == "C02"
    failed_ops = {s["name"] for s in bad["steps"] if s["status"] == "failed"}
    meta = next(m for m in metas if m["status"] == "error")
    assert failed_ops == {k.split(".")[-1] for k in meta["errors"]}  # the drawer shows the trace's failed op
    assert all("inputs" not in s and "outputs" not in s for i in detail["items"] for s in i["steps"])


def test_the_consolidator_state_matches_what_its_traces_report(traced, monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_COPILOT", "scripted-model")
    m = Model(RuntimeError("provider down"), {"items": [{"kind": "goal", "text": "Mua nhà", "same_as": None}]})
    monkeypatch.setattr("operonx.providers.ops._utils.resolve_hub", lambda: m)
    talk(*TALK)

    assert job("assistant_consolidate").status == "ok"  # the job ran; the conversation it read did not go well
    (meta,) = traces("assistant_consolidate")
    assert meta["status"] == "ok" and json.loads(meta["output"])["consolidated"]["failed"] == 1
    assert node("consolidator")["state"] == "failed"

    assert job("assistant_consolidate").status == "ok"  # the next tick retries it
    (meta,) = traces("assistant_consolidate")
    assert json.loads(meta["output"])["consolidated"]["done"] == 1
    n = node("consolidator")
    assert n["state"] == "done" and n["conversations"] == {"runs": 2, "failed": 1} and n["cost"] == 0.0011
    shown = ecosystem.runs("consolidator")
    assert [r["state"] for r in shown["conversations"]] == ["done", "failed"]
    assert "Mua nhà" not in json.dumps(shown, ensure_ascii=False)  # counts, never what was kept


def test_the_cio_desk_states_match_the_worker_trace(traced):
    ev = event(*GOLD)
    queue.enqueue(ev["id"], "cio")
    assert node("queue")["state"] == "waiting" and node("cio")["state"] == "idle"

    assert job("agent_worker").status == "ok"
    (meta,) = traces("agent_worker")
    ran = json.loads(meta["output"])["job"]
    assert meta["status"] == "ok" and ran["status"] == "done"
    assert node("queue")["state"] == "done"
    assert node("cio")["state"] == node("challenger")["state"] == "done"

    (row,) = ecosystem.runs("cio")["runs"]
    steps = ecosystem.run("cio", row["id"])["steps"]
    assert steps and all(s["status"] == "done" for s in steps)
    assert all("prompt" not in s and "output" not in s for s in steps)


def test_the_assistant_state_comes_from_its_audited_turns():
    ask = Operon(assistant_flow, params={k: None for k in ("message", "role", "client_id", "scope", "route", "goals",
                                                            "turn_id", "approvals", "conversation_id")})  # fmt: skip
    assert node("assistant")["state"] == "idle"
    out = asyncio.run(ask.run(inputs={"message": "tổng quan tài sản", "role": "client", "client_id": "C01",
                                      "scope": "personal", "route": "#/client/tong-quan"}))  # fmt: skip
    a = out["assistant"]
    assert a["mode"] == "fallback" and a["status"] == "ok"  # MF_AI off: the keyword path
    for n in ("assistant", "fallback", "tools_app"):
        assert node(n)["state"] == "done" and node(n)["day"] == {"runs": 1, "failed": 0}, n
    assert node("tools_memory")["state"] == "idle"
    (row,) = ecosystem.runs("assistant")["runs"]
    assert row["id"] == f"T{a['audit_seq']}" and "tổng quan" not in json.dumps(row, ensure_ascii=False)
    detail = ecosystem.run("assistant", row["id"])
    assert [s["note"] for s in detail["steps"]] == [s["tool"] for s in a["steps"]]


def test_the_map_is_served_to_the_desk():
    with TestClient(Application.find(".").asgi()) as c:
        m = c.get("/api/agents/map").json()
        assert {n["id"] for n in m["nodes"]} == {n["id"] for n in ecosystem.NODES} and m["edges"] == ecosystem.EDGES
        assert c.get("/api/agents/map/assistant").json()["runs"] == []
        assert c.get("/api/agents/map/nope").status_code == 404
        assert c.get("/api/agents/map/cio?run=AG-999999").status_code == 404

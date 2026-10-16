"""BRD §5 time limits (BRD-RULE-WF-03: the CIO agent within 15 minutes; WF-04: the challenger within 5), enforced
on every live model call of a run: a call is cut at what is left of its run's time, and a run past its limit fails
with why — the view goes to AGENT_ERROR, or keeps its draft with the challenger's error to run again."""

import asyncio
import json
from types import SimpleNamespace

import pytest
from test_views import GOLD, FakeLLM, agent, event

from control import db
from views import agents
from views import store as vstore


class SlowLLM(FakeLLM):
    def __init__(self, *a, delay=0.0, **k):
        super().__init__(*a, **k)
        self.delay = delay

    async def generate(self, messages, **kw):
        await asyncio.sleep(self.delay)
        return await super().generate(messages, **kw)


@pytest.fixture
def slow(monkeypatch):
    monkeypatch.setenv("MF_AI", "on")
    monkeypatch.setenv("LLM_MODEL_CIO", "vendor/big-model")
    monkeypatch.setenv("LLM_MODEL_CHALLENGER", "vendor/small-model")
    sent = []
    llms = {
        "llm:cio": SlowLLM("vendor/big-model", sent),
        "llm:challenger": SlowLLM("vendor/small-model", sent),
    }
    import operonx.providers.ops._utils as hub_utils

    monkeypatch.setattr(hub_utils, "resolve_hub", lambda: SimpleNamespace(get=lambda key: llms[key]))
    return llms


def test_the_limits_are_the_brds():
    assert agents.DEADLINES["cio"] == 15 * 60 and agents.DEADLINES["challenger"] == 5 * 60


def test_a_cio_agent_run_past_its_limit_fails_with_why(slow, monkeypatch):
    monkeypatch.setitem(agents.DEADLINES, "cio", 1)  # 15 minutes, scaled to a second
    slow["llm:cio"].delay = 3
    v = agent(event(*GOLD)["id"])["view"]
    assert v["status"] == "AGENT_ERROR"
    assert "Quá thời hạn" in json.dumps(vstore.get(v["id"])["error"], ensure_ascii=False)
    [run] = [r for r in vstore.runs(v["id"]) if r["agent"] == "cio"]
    assert run["status"] == "error" and run["finished"] - run["created"] < 3  # cut, not waited out


def test_a_challenger_past_its_limit_leaves_the_draft_with_its_error(slow, monkeypatch):
    monkeypatch.setitem(agents.DEADLINES, "challenger", 1)
    slow["llm:challenger"].delay = 3
    v = agent(event(*GOLD)["id"])["view"]
    kept = vstore.get(v["id"])
    assert kept["status"] == "PENDING_CHALLENGE" and kept["current"] and "Quá thời hạn" in kept["challenge_error"]
    ch = [r for r in vstore.runs(v["id"]) if r["agent"] == "challenger"]
    assert ch and ch[-1]["status"] == "error"


def test_a_run_already_past_its_time_makes_no_call(slow):
    rid = vstore.start_run("challenger", "VW-x", "live", "vendor/small-model")
    with db.tx() as con:
        con.execute("update agent_runs set created = created - 400 where id = ?", (rid,))
    with pytest.raises(agents.AgentError, match="5 phút"):
        asyncio.run(agents.call_model("challenger", "s", "u", 100, run_id=rid))
    assert not slow["llm:challenger"].sent

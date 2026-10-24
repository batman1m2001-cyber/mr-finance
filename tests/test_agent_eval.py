"""AGENT_EVALUATION_PLAN: what the news agents cost, what the collection brings in, and whether the agents' calls
were right (and worth what, on the simulated book). Each test builds its own rows; no model is called."""

import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from views import agents

ROOT = Path(__file__).resolve().parents[1]


def _bridge():
    spec = importlib.util.spec_from_file_location("claude_bridge", ROOT / "scripts" / "claude_bridge.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# -- cost (§3) --------------------------------------------------------------------------------------------------


def _resp(**usage):
    return SimpleNamespace(usage=SimpleNamespace(**usage) if usage else None)


def test_a_call_with_no_reported_cost_records_none_never_zero():
    meta = agents.usage_meta(_resp(prompt_tokens=100, completion_tokens=20), "m")
    assert meta["cost_usd"] is None and meta["cost_kind"] is None
    assert (meta["tokens_in"], meta["tokens_out"], meta["tokens_cached"]) == (100, 20, 0)
    none = agents.usage_meta(_resp(), "m")
    assert none["tokens_in"] is None and none["tokens_cached"] is None and none["cost_usd"] is None


def test_the_provider_cost_and_the_bridge_notional_cost_are_kept_apart():
    paid = agents.usage_meta(_resp(prompt_tokens=10, completion_tokens=2, cost=0.0012), "m")
    assert (paid["cost_usd"], paid["cost_kind"]) == (0.0012, "provider")
    notional = agents.usage_meta(
        _resp(
            prompt_tokens=10,
            completion_tokens=2,
            cost=0.5,
            cost_kind="notional",
            prompt_tokens_details=SimpleNamespace(cached_tokens=7),
        ),
        "m",
    )
    assert (notional["cost_usd"], notional["cost_kind"], notional["tokens_cached"]) == (0.5, "notional", 7)
    free = agents.usage_meta(_resp(prompt_tokens=1, completion_tokens=1, cost=0), "m")
    assert free["cost_usd"] == 0.0 and free["cost_kind"] == "provider"  # a reported zero stays a zero


def test_the_bridge_finds_claude_on_each_call_and_answers_a_missing_binary_with_a_reason(monkeypatch, tmp_path):
    bridge = _bridge()
    gone = tmp_path / "gone" / "claude"
    monkeypatch.setattr(bridge, "find_claude", lambda: str(gone))  # the extension folder removed (2026-10-24)
    with pytest.raises(RuntimeError, match="did not start"):
        asyncio.run(bridge.Bridge(1).ask("claude-haiku-5-5", "", "hi"))
    monkeypatch.undo()
    monkeypatch.setattr(bridge.shutil, "which", lambda _: None)
    monkeypatch.setattr(bridge.glob, "glob", lambda _: [])
    with pytest.raises(RuntimeError, match="not found"):
        bridge.find_claude()

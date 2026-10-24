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


# -- collection (§2.1) ------------------------------------------------------------------------------------------

NOW = 1_792_000_000.0  # 2026-10-14


def _feed(*items):
    from test_news import feed, rfc

    return feed(*((t, link, d, rfc(p) if p else None) for t, link, d, p in items))


def _ingest(feeds, now=NOW):
    from test_news import ingest

    return ingest(feeds, now)


def _last():
    from news import store

    return store.last_run()


def test_a_run_records_its_funnel_status_sources_and_groups():
    kd = _feed(
        ("Ngân hàng Nhà nước tăng lãi suất điều hành", "https://vnexpress.net/a.html", "Tóm tắt", NOW - 600),
        ("Giá vàng SJC lập đỉnh", "https://vnexpress.net/b.html", "", NOW - 600),  # no summary
        ("Một quán cà phê mới mở", "https://vnexpress.net/c.html", "x", NOW - 600),  # low, unclassified
        ("Tin không giờ", "https://vnexpress.net/d.html", "x", None),  # refused: no publication time
        ("Tin cũ", "https://vnexpress.net/e.html", "x", NOW - 30 * 86400),  # too old: skipped
    )
    do = _feed(("Giá nhà chung cư Hà Nội tiếp tục tăng", "https://vneconomy.vn/f.htm", "x", NOW - 600))
    _ingest({"vnexpress_kd": kd, "vneconomy_do": do, "cafef_ck": "<not xml"})
    r = _last()
    assert (r["fetched"], r["skipped"], r["duplicates"], r["unique"]) == (6, 1, 0, 5)  # fetched = skipped+dup+unique
    assert (r["refused"], r["retained"], r["added"], r["relevant"]) == (1, 4, 4, 3)  # unique = refused+retained
    assert (r["status"], r["attempted"], r["succeeded"], r["failed"]) == ("partial", 3, 2, 1)
    assert list(r["failed_sources"]) == ["cafef_ck"] and r["configured"] >= 11
    assert r["by_category"] == {"real_estate": 1, "stocks": 0, "policy_macro": 1, "other": 1, "unclassified": 1}
    assert r["missing"] == {"published": 1, "summary": 1, "category": 1}
    assert r["at"] == NOW and r["started"] and r["finished"] >= r["started"] and r["duration_s"] >= 0


def test_a_second_run_counts_the_same_news_as_duplicates_once_and_none_as_new():
    kd = _feed(("Ngân hàng Nhà nước tăng lãi suất điều hành", "https://vnexpress.net/a.html", "x", NOW - 600))
    _ingest({"vnexpress_kd": kd})
    _ingest({"vnexpress_kd": kd}, NOW + 600)
    r = _last()
    assert (r["fetched"], r["duplicates"], r["unique"], r["retained"], r["relevant"]) == (1, 1, 0, 0, 0)
    assert r["status"] == "ok"


def test_a_run_where_every_source_failed_is_failed():
    _ingest({"vnexpress_kd": "<x", "cafef_ck": "<y"})
    r = _last()
    assert (r["status"], r["succeeded"], r["failed"], r["fetched"]) == ("failed", 0, 2, 0)


def test_an_old_run_reads_what_it_kept_and_none_for_the_rest():
    from news import monitor, store

    store.record_run(
        {
            "at": NOW,
            "added": 3,
            "refused": 1,
            "duplicates": 5,
            "held": 0,
            "sources": {
                "a": {"fetched": 9, "accepted": 8, "refused": 1, "skipped": 0, "error": None},
                "b": {"fetched": 0, "accepted": 0, "refused": 0, "skipped": 0, "error": "URLError: x"},
            },
        }
    )
    [r] = monitor.runs(NOW - 1, NOW + 1)
    assert (r["fetched"], r["unique"], r["retained"], r["status"], r["failed"]) == (9, 4, 3, "partial", 1)
    assert r["started"] is None and r["relevant"] is None and r["by_category"] is None and r["missing"] is None
    assert r["full"] is False


def test_the_days_count_by_collection_time_never_publication_time_and_say_none_for_unkept_fields():
    from news import monitor, store

    # published three days earlier, collected today: it is today's collection
    kd = _feed(("Ngân hàng Nhà nước tăng lãi suất điều hành", "https://vnexpress.net/a.html", "x", NOW - 3 * 86400))
    _ingest({"vnexpress_kd": kd})
    store.record_run({"at": NOW - 86400, "added": 0, "refused": 0, "duplicates": 2, "held": 0, "sources": {}})
    today, yesterday, *_ = monitor.days(3, NOW + 60)
    assert today["day"] == monitor.day_of(NOW) and today["retained"] == 1 and today["relevant"] == 1
    assert today["by_category"]["policy_macro"] == 1 and today["lag_min_p50"] == 3 * 24 * 60
    assert today["fetched"] == 1 and today["runs_ok"] == 1
    assert yesterday["retained"] == 0 and yesterday["runs_failed"] == 1  # an old run that tried no source
    s = monitor.summary(3, NOW + 60)
    assert s["full_since"] == NOW and s["last_run"]["retained"] == 1

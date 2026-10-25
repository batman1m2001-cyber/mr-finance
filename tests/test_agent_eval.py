"""AGENT_EVALUATION_PLAN: what the news agents cost, what the collection brings in, and whether the agents' calls
were right (and worth what, on the simulated book). Each test builds its own rows; no model is called."""

import asyncio
import importlib.util
from collections import Counter
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


def test_the_days_sum_the_collection_time_and_keep_the_first_and_last_run():
    from news import monitor, store

    for at, secs in ((NOW + 100, 30.0), (NOW + 4000, 12.5)):
        store.record_run(
            {"at": at, "started": at, "finished": at + secs, "duration_s": secs, "added": 0, "refused": 0,
             "duplicates": 0, "held": 0, "sources": {}}
        )  # fmt: skip
    store.record_run({"at": NOW + 2000, "added": 0, "refused": 0, "duplicates": 0, "held": 0, "sources": {}})  # old
    [today] = monitor.days(1, NOW + 5000)
    assert today["duration_s_total"] == 42.5 and today["duration_runs"] == 2 and today["runs"] == 3
    assert today["first_run"] == NOW + 100 and today["last_run"] == NOW + 4012.5


def test_a_news_item_reached_a_portfolio_through_an_approved_view_and_never_through_a_zero_ranking(monkeypatch):
    from test_apply import MARKET, approved

    from apply import run as apply_run
    from news import monitor

    _, run = approved(*MARKET)
    hit = {f["family_id"] for f in run["ranking"] if f["expected_3m"]}
    [today] = monitor.days(1, NOW + 60)
    assert today["portfolio"] == 2 and today["portfolio_families"] == len(hit) > 0
    flat = [{**run, "ranking": [{**f, "expected_3m": 0.0} for f in run["ranking"]]}]
    monkeypatch.setattr(apply_run, "runs", lambda statuses=None: flat)
    assert monitor.reached() == {} and monitor.days(1, NOW + 60)[0]["portfolio"] == 0


# -- accuracy (§2.2–2.5) ----------------------------------------------------------------------------------------

CFG = {"material_sigma": 1.0, "claim_share": 0.25}
ORIGIN, TODAY = "2026-10-21", "2026-10-30"  # the 1w move from the 10-22 morning is due 10-28


class _Series:
    """A factor's realised move: ``x`` from the origin to any day up to ``last``."""

    def __init__(self, x, last="2026-10-29"):
        self.x, self.last = x, last

    def move(self, d0, d1):
        return self.x


def _factor(fid="VNINDEX", vol=4.0, assumed=False):
    return SimpleNamespace(id=fid, unit="pct", vol_month=vol, assumed=assumed)


def _draft(expected, view="VW-1", created=1792650000.0):  # 2026-10-22, the day after the origin
    return {
        "view_id": view,
        "event_id": "EV-1",
        "origin": ORIGIN,
        "created": created,
        "expected": expected,
        "p10": expected - 3,
        "p90": expected + 3,
    }


def _judge(drafts, x=None, ran=True, today=TODAY, factor=None, cfg=CFG, last="2026-10-29"):
    from trial import evaluate

    f = factor or _factor()
    series = {} if x is None else {f.id: _Series(x, last)}
    return evaluate.judge_move("2026-10-22", "1w", f, drafts, ran, series, today, cfg, 0.25)
    # scale = 4 · √0.25 = 2: a material move is |x| ≥ 2, a material claim |e| ≥ 0.5


def test_each_verdict_from_a_claim_and_the_move():
    assert _judge([_draft(1.0)], x=2.5)["verdict"] == "correct"
    wrong = _judge([_draft(1.0)], x=-2.5)
    assert (wrong["verdict"], wrong["reason"], wrong["direction_hit"]) == ("incorrect", "wrong_direction", False)
    small = _judge([_draft(1.0)], x=0.4)  # the move came, too small to be the call's
    assert (small["verdict"], small["reason"], small["direction_hit"]) == ("incorrect", "not_material", True)
    missed = _judge([_draft(0.1)], x=-3.0)  # no claim, a material move
    assert (missed["verdict"], missed["reason"]) == ("missed", "not_predicted")
    assert _judge([_draft(0.1)], x=0.3)["verdict"] == "quiet"
    assert _judge([], x=3.0, ran=False)["reason"] == "no_run"  # a morning with no drafts
    got = _judge([_draft(1.0)], x=2.5)
    assert got["error"] == 1.5 and got["error_sd"] == 0.75 and got["inside"] and got["due"] == "2026-10-28"


def test_a_pending_move_is_never_incorrect_and_no_data_is_failed_only_after_the_give_up_days():
    assert _judge([_draft(1.0)], x=-2.5, today="2026-10-27")["verdict"] == "pending"  # not due
    waiting = _judge([_draft(1.0)], x=-2.5, last="2026-10-27")  # due, the data not in yet
    assert (waiting["verdict"], waiting["reason"]) == ("pending", "waiting")
    gone = _judge([_draft(1.0)], x=-2.5, last="2026-10-27", today="2026-12-01")
    assert (gone["verdict"], gone["reason"]) == ("failed", "no_data")
    assert _judge([_draft(1.0)])["reason"] == "no_series"  # nothing to score against: excluded
    assert _judge([_draft(1.0)], factor=_factor(assumed=True))["reason"] == "assumed"


def test_duplicate_drafts_of_one_move_are_scored_once_and_opposite_claims_are_conflicting():
    two = _judge([_draft(1.0, "VW-1"), _draft(2.0, "VW-2")], x=2.5)
    assert two["verdict"] == "correct" and two["expected"] == 1.5 and len(two["drafts"]) == 2
    both = _judge([_draft(1.0, "VW-1"), _draft(-1.0, "VW-2")], x=2.5)
    assert (both["verdict"], both["reason"], both["claim"]) == ("excluded", "conflicting", "conflicting")
    one_quiet = _judge([_draft(1.0, "VW-1"), _draft(-0.1, "VW-2")], x=2.5)  # a quiet draft does not conflict
    assert one_quiet["claim"] == "up" and one_quiet["verdict"] == "correct"


def test_a_draft_made_on_or_before_its_origin_close_is_excluded_as_a_leak():
    leak = _judge([_draft(1.0, created=1792540000.0)], x=2.5)  # 2026-10-20, before the 10-21 close it is scored from
    assert (leak["verdict"], leak["reason"], leak["leak"]) == ("excluded", "leak", ["VW-1"])


def test_the_materiality_threshold_comes_from_the_settings():
    assert _judge([_draft(0.1)], x=1.5)["verdict"] == "quiet"
    assert _judge([_draft(0.1)], x=1.5, cfg={**CFG, "material_sigma": 0.5})["verdict"] == "missed"
    got = _judge([_draft(0.1)], x=1.5, cfg={**CFG, "material_sigma": 0.5})
    assert got["material_sigma"] == 0.5 and got["scale"] == 2.0  # the record keeps what it was scored with


def test_the_rates_carry_their_counts_and_leave_pending_out():
    from trial import evaluate

    rows = [
        {"verdict": "correct", "direction_hit": True, "error_sd": 0.5},
        {"verdict": "incorrect", "reason": "wrong_direction", "direction_hit": False, "error_sd": 1.5},
        {"verdict": "incorrect", "reason": "not_material", "direction_hit": True, "error_sd": 0.2},
        {"verdict": "missed", "reason": "not_predicted", "direction_hit": False, "error_sd": 1.0},
        {"verdict": "missed", "reason": "no_run"},
        {"verdict": "quiet", "direction_hit": True, "error_sd": 0.1},
        {"verdict": "pending", "reason": "not_due"},
        {"verdict": "excluded", "reason": "conflicting"},
    ]
    r = evaluate.rates(rows)
    assert r["precision"] == {"value": 0.333, "hits": 1, "n": 3}
    assert r["recall"] == {"value": 0.333, "hits": 1, "n": 3}  # correct + wrong direction + not predicted
    assert r["recall_all"]["n"] == 4  # and the morning that did not run
    assert r["direction"] == {"value": 0.6, "hits": 3, "n": 5}
    assert r["error_sd"] == {"value": 0.66, "n": 5}
    assert r["coverage"] == {
        "moves": 8,
        "due": 7,
        "scored": 6,
        "pending": 1,
        "failed": 0,
        "excluded": 1,
        "excluded_by": {"conflicting": 1},
    }
    empty = evaluate.rates([{"verdict": "pending", "reason": "not_due"}])
    assert empty["precision"] == {"value": None, "hits": 0, "n": 0}  # no denominator, no rate


def test_the_timeline_adds_up_by_due_day_and_leaves_pending_out():
    from trial import evaluate

    rows = [
        {"verdict": "correct", "direction_hit": True, "due": "2026-10-24"},
        {"verdict": "missed", "reason": "not_predicted", "due": "2026-10-24"},
        {"verdict": "incorrect", "reason": "wrong_direction", "direction_hit": False, "due": "2026-10-25"},
        {"verdict": "pending", "reason": "not_due", "due": "2026-10-26"},  # not a day on the chart
        {"verdict": "excluded", "reason": "conflicting", "due": "2026-10-26"},
    ]
    t = evaluate.timeline(rows)
    assert [d["day"] for d in t] == ["2026-10-24", "2026-10-25"]
    assert t[0]["precision"] == {"value": 1.0, "hits": 1, "n": 1} and t[0]["recall"]["n"] == 2
    assert t[1]["precision"] == {"value": 0.5, "hits": 1, "n": 2} and t[1]["scored"] == 3  # cumulative
    assert evaluate.timeline([{"verdict": "pending", "due": "2026-10-26"}]) == []


def test_a_failed_grouping_call_is_recorded_on_the_morning_and_raised(monkeypatch):
    from test_views import NOW, news

    from trial import daily, evaluate

    async def broken(*a, **k):
        raise RuntimeError("InternalServerError")

    monkeypatch.setattr(agents, "resolve_mode", lambda requested: "live")
    monkeypatch.setattr(agents, "call_model", broken)
    news("NHNN giữ nguyên lãi suất điều hành")
    with pytest.raises(RuntimeError):
        asyncio.run(daily.run(now=NOW + 3600))
    day = __import__("datetime").date.fromtimestamp(NOW + 3600).isoformat()
    note = daily.notes()[day]
    assert note["status"] == "failed" and note["stage"] == "group" and "InternalServerError" in note["error"]
    tomorrow = evaluate.shadow.realised.add_days(day, 1)
    [m] = [m for m in evaluate.mornings(tomorrow) if m["day"] == day]
    assert m["status"] == "failed" and m["drafts"] == 0


def test_scoring_freezes_final_verdicts_and_recomputes_pending_ones(monkeypatch):
    from control import db
    from trial import daily, evaluate

    day = "2026-10-22"
    daily.note_day(day, status="failed", error="x")
    monkeypatch.setattr(daily, "until", lambda: "2026-10-31")
    flat = {f.id: _Series(0.0, "2027-03-01") for f in evaluate.shadow.model().factors}
    evaluate.score("2026-10-26", flat)  # the 10-22 3d move came due 10-24: scored; its 1w and 3m pending
    n = len(evaluate.shadow.model().factors)
    mine = lambda: Counter(r["verdict"] for r in evaluate.scores(day))  # noqa: E731
    assert mine() == {"quiet": n, "pending": 2 * n}
    s = evaluate.get(f"{day}:3d:VNINDEX")
    assert (s["verdict"], s["morning"], s["origin"], s["due"]) == ("quiet", "failed", "2026-10-21", "2026-10-24")
    later = [m["status"] for m in evaluate.mornings("2026-10-26")]
    assert later == ["failed", "no_record", "no_record", "no_record"]  # 10-26 itself is still to run
    big = {f.id: _Series(100.0, "2027-03-01") for f in evaluate.shadow.model().factors}
    evaluate.score("2026-10-30", big)  # the 3d verdicts stay; the 1w ones come due, missed with no run
    assert mine() == {"quiet": n, "missed": n, "pending": n}
    assert evaluate.get(f"{day}:1w:VNINDEX")["reason"] == "no_run"
    with db.tx() as con:
        assert con.execute("select count(*) from eval_scores where day = ?", (day,)).fetchone()[0] == 3 * n


def test_event_recall_says_where_each_important_story_was_lost():
    import json

    from news import store
    from trial import daily, evaluate

    kd = _feed(
        ("Ngân hàng Nhà nước tăng lãi suất điều hành", "https://vnexpress.net/a.html", "x", NOW - 3600),
        ("Giá vàng SJC lập đỉnh mới", "https://vnexpress.net/b.html", "x", NOW - 1800),
        ("Một quán cà phê mới mở", "https://vnexpress.net/c.html", "x", NOW - 1200),
    )
    _ingest({"vnexpress_kd": kd})
    ids = {i["title"]: i["id"] for i in store.inbox(status="all", limit=None)}
    rate, gold, cafe = (
        ids["Ngân hàng Nhà nước tăng lãi suất điều hành"],
        ids["Giá vàng SJC lập đỉnh mới"],
        ids["Một quán cà phê mới mở"],
    )
    daily._keep("EV-1", "2026-10-14", {"created": NOW, "news_ids": [rate], "view_id": "VW-1"})
    with store._db() as con:
        for k, (nid, at) in enumerate(((rate, NOW - 3600), (gold, NOW - 1800), (cafe, NOW - 1200), (rate, NOW + 60))):
            data = {"title": f"story {k}", "important": True, "match": {"score": 0.9, "news_id": nid}}
            con.execute(
                "insert into reference_stories values (?, ?, ?, ?, 1, ?)", (f"R{k}", at, at, NOW, json.dumps(data))
            )
    got = evaluate.event_recall()
    assert (got["hits"], got["n"], got["value"]) == (1, 3, 0.333)  # the story after the run is not this morning's
    assert {m["news_id"]: m["why"] for m in got["misses"]} == {gold: "not_grouped", cafe: "not_candidate"}


# -- money (§2.6) -----------------------------------------------------------------------------------------------

FAMS = {
    "C01": {
        "name": "A",
        "holdings": [
            {
                "key": "s",
                "owner": "a",
                "kind": "asset",
                "class": "stock",
                "name": "VNM",
                "value": 1_000_000_000,
                "detail": {"ticker": "VNM", "beta": 1.0},
            }
        ],
    },
    "C02": {"name": "B", "holdings": []},
}


def _scored(verdict, x, expected=1.0, factor="VNINDEX", day="2026-10-22"):
    return {
        "day": day,
        "horizon": "1w",
        "factor": factor,
        "verdict": verdict,
        "realised": x,
        "expected": expected,
        "family": "stocks",
    }


def test_the_book_is_frozen_once_per_morning_and_a_late_one_says_so():
    from trial import finance

    assert asyncio.run(finance.keep("2026-10-22", families=FAMS))
    assert not asyncio.run(finance.keep("2026-10-22", late=True, families={}))  # frozen: the first stays
    snap = finance.snapshot("2026-10-22")
    vn = snap["exposure"]["1w"]["C01"]["VNINDEX"]
    assert vn == 10_000_000 and snap["late"] is False  # 1 % of VND 1 bn at beta 1, per 1 % VN-Index move
    assert "C02" in snap["exposure"]["1w"] and snap["exposure"]["1w"]["C02"] == {}
    asyncio.run(finance.keep("2026-10-23", late=True, families=FAMS))
    assert finance.snapshot("2026-10-23")["late"] is True


def test_vnd_by_hand_correct_incorrect_missed_and_a_negative_warning():
    from trial import finance

    asyncio.run(finance.keep("2026-10-22", families=FAMS))
    rows = [
        _scored("correct", 2.5),  # +25 m
        _scored("correct", -3.0, expected=-1.0),  # +30 m, and it hurt the family: a negative warning
        _scored("incorrect", -2.0),  # −20 m
        _scored("missed", 4.0, expected=0.1),  # 40 m missed, not netted
        _scored("quiet", 0.5, expected=0.0),
        {**_scored("pending", None), "realised": None},  # adds nothing
        _scored("correct", 2.5, day="2026-10-24"),  # no snapshot: unavailable, never 0
    ]
    t = finance.summary(rows)["horizons"]["1w"]
    assert t["correct"] == {"vnd": 55_000_000, "n": 2}
    assert t["incorrect"] == {"vnd": 20_000_000, "n": 1}
    assert t["net"] == {"vnd": 35_000_000, "n": 3}
    assert t["negative_warnings"] == {"vnd": 30_000_000, "n": 1}
    assert t["missed_opportunity"] == {"vnd": 40_000_000, "n": 1}
    assert t["effect"]["vnd"] == 25_000_000 - 30_000_000 - 20_000_000 + 40_000_000 + 5_000_000
    assert (t["scored"], t["unavailable"], t["late"]) == (6, 1, 0)
    assert t["by_family"]["stocks"]["net"]["vnd"] == 35_000_000 and t["by_family"]["policy_macro"]["net"]["n"] == 0
    assert finance.value(rows[0], None) is None


def test_the_vnd_timeline_adds_up_per_group_by_due_day():
    from trial import finance, segments

    asyncio.run(finance.keep("2026-10-22", families=FAMS))
    rows = [
        {**_scored("correct", 2.5), "due": "2026-10-29"},  # +25 m
        {**_scored("incorrect", -2.0), "due": "2026-10-29"},  # −20 m
        {**_scored("missed", 4.0, expected=0.1), "due": "2026-10-30"},  # 0 on the net, still a scored move
        {**_scored("correct", 3.0, day="2026-10-24"), "due": "2026-10-30"},  # no snapshot: not on the chart
        {**_scored("pending", None), "realised": None, "due": "2026-10-31"},
    ]
    t = finance.summary(rows)["horizons"]["1w"]["timeline"]
    zero = {g: 0 for g in segments.FAMILIES}
    assert t == [
        {"day": "2026-10-29", "by_family": {**zero, "stocks": 5_000_000}, "n": 2},
        {"day": "2026-10-30", "by_family": {**zero, "stocks": 5_000_000}, "n": 3},
    ]


# -- cost per agent (§3) ----------------------------------------------------------------------------------------


def _line(at, model="claude-sonnet-5-5", i=100, o=20, usd=0.01, error=None):
    return {
        "at": at,
        "asked": f"anthropic/{model.replace('-5-5', '-5.5')}",
        "model": model,
        "s": 1.0,
        "usage": {"in": i, "out": o, "usd": usd},
        "error": error,
    }


def test_the_backfill_matches_exactly_one_bridge_line_or_none():
    from trial import costs

    call = {"model": "anthropic/claude-sonnet-5.5", "tokens_in": 100, "tokens_out": 20}
    assert costs.match(call, [_line(10.0)], (0, 20))["usage"]["usd"] == 0.01
    assert costs.match(call, [_line(10.0), _line(12.0)], (0, 20)) is None  # two the same: none
    assert costs.match(call, [_line(30.0)], (0, 20)) is None  # outside the run
    assert costs.match(call, [_line(10.0, model="claude-opus-5-5")], (0, 20)) is None
    assert costs.match(call, [_line(10.0, i=101)], (0, 20)) is None
    assert costs.match(call, [_line(10.0, error="x")], (0, 20)) is None
    grouped = {"model": "anthropic/claude-sonnet-5.5", "tokens_in": None, "tokens": 120}  # only in + out was kept
    assert costs.match(grouped, [_line(10.0)], (0, 20)) is not None


def test_cost_per_agent_counts_the_calls_that_reported_one_and_never_reads_none_as_zero():
    from trial import costs

    rows = [
        {
            "agent": "cio",
            "tokens_in": 10,
            "tokens_out": 5,
            "tokens": 15,
            "tokens_cached": None,
            "cost_usd": 0.02,
            "cost_kind": "notional",
            "ms": 1000,
            "attempt": 1,
            "error": None,
            "model": "m",
        },
        {
            "agent": "cio",
            "tokens_in": 10,
            "tokens_out": 5,
            "tokens": 15,
            "tokens_cached": 3,
            "cost_usd": None,
            "cost_kind": None,
            "ms": 3000,
            "attempt": 2,
            "error": "AgentError",
            "model": "m",
        },
        {
            "agent": "challenger",
            "tokens_in": None,
            "tokens_out": None,
            "tokens": None,
            "tokens_cached": None,
            "cost_usd": None,
            "cost_kind": None,
            "ms": None,
            "attempt": 1,
            "error": None,
            "model": "n",
        },
    ]
    a = costs.per_agent(rows)
    assert (a["cio"]["cost_usd"], a["cio"]["n_reported"], a["cio"]["n_calls"]) == (0.02, 1, 2)
    assert (a["cio"]["retries"], a["cio"]["errors"], a["cio"]["ms_p50"], a["cio"]["tokens"]) == (1, 1, 2000.0, 30)
    assert a["challenger"]["cost_usd"] is None and a["challenger"]["n_tokens"] == 0  # unavailable, not 0

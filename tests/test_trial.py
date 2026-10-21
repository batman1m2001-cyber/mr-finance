"""The news agents' trial (BUSINESS_FEEDBACK_1021_PLAN B1, src/trial): a morning groups the news into events by the
CIO model, runs the agents on each as agent:trial, keeps every draft's shadow forecasts, and the report scores them.
The model here is a fake grouping and the keyword agent (mock): no model call."""

import asyncio
import json
from datetime import date, datetime, timedelta

import pytest
from test_views import AGENT, NOW, news

from control import roles
from control.roles import TRIAL_ACTOR
from events import store as events
from measure import realised
from trial import daily, report, shadow
from views import agents
from views import store as vstore

DAY = date.fromtimestamp(NOW).isoformat()


@pytest.fixture
def morning(monkeypatch):
    """The agents live as far as the trial can tell, the grouping faked, the agent the keyword one."""
    asked = []

    async def fake_group(resource, system, user, max_tokens, run_id=None):
        data = json.loads(user.split("DỮ_LIỆU\n", 1)[1].rsplit("\nHẾT_DỮ_LIỆU", 1)[0])
        ids = [n["id"] for n in data["news"]]
        asked.append(ids)
        out = {"events": [{"title": "NHNN giữ lãi suất", "news": ids[:2] + ["NW-999999"], "segment": "macro",
                           "why": "VN_RATE"}, {"title": "", "news": ids[2:]}]}
        return json.dumps(out), {"model": "fake", "tokens_in": 100, "tokens_out": 20}

    async def keyword_agent(event_id):
        out = await AGENT.run(inputs={"event_id": event_id, "by": TRIAL_ACTOR, "mode": "mock"})
        assert "$errors" not in out, out["$errors"]
        return {"view_id": out["result"]["view"]["id"], "error": None}

    monkeypatch.setattr(agents, "resolve_mode", lambda requested: requested or "live")
    monkeypatch.setattr(agents, "call_model", fake_group)
    monkeypatch.setattr(daily, "run_agent", keyword_agent)
    return asked


def test_a_morning_groups_the_news_runs_the_agents_and_keeps_shadow_forecasts(morning):
    ids = news("NHNN giữ nguyên lãi suất điều hành", "Lãi suất liên ngân hàng giảm", "Fed họp về lãi suất")
    got = asyncio.run(daily.run(now=NOW + 3600))
    assert morning and set(ids) <= set(morning[0])
    [made] = got["made"]
    assert made["status"] == "PENDING_APPROVAL" and made["segment"] == "macro"
    ev = events.get(made["event_id"])
    assert ev["created_by"] == TRIAL_ACTOR and ev["news_ids"] == morning[0][:2]  # the unknown id dropped
    view = vstore.get(made["view_id"])
    assert view["status"] == "PENDING_APPROVAL"  # nothing approved
    rows = shadow.rows()
    assert len(rows) == 15 * 3 and {r["horizon"] for r in rows} == {"3d", "1w", "3m"}
    vn = next(r for r in rows if r["factor"] == "VNINDEX" and r["horizon"] == "1w")
    made_day = datetime.fromtimestamp(view["created"]).date()
    assert vn["origin"] == (made_day - timedelta(days=1)).isoformat()  # the close before the agents ran
    assert vn["due"] == realised.add_days(vn["origin"], 7) and vn["segment"] == "macro"
    assert vn["call"] in ("mua", "bán", "giữ") and len(vn["branches"]) == len(view["current"]["scenarios"]["branches"])
    assert next(r for r in rows if r["factor"] == "VN_RATE")["call"] is None  # a reading only for what clients hold
    assert shadow.record(view, {}) == 0 and daily.record_missing() == []  # once
    again = asyncio.run(daily.run(now=NOW + 7200))
    assert again["made"] == [] and again["reason"] == "Đã chạy hôm nay"


def test_the_trial_ends_on_its_day_and_never_runs_the_mock(morning, monkeypatch):
    monkeypatch.setenv("MF_TRIAL_UNTIL", "2020-01-01")
    assert "kết thúc" in asyncio.run(daily.run(now=NOW))["reason"]
    monkeypatch.delenv("MF_TRIAL_UNTIL")
    monkeypatch.setattr(agents, "resolve_mode", lambda requested: "mock")
    assert "mô phỏng" in asyncio.run(daily.run(now=NOW))["reason"] and daily.days() == {}


def test_the_report_scores_the_shadow_forecasts_the_readings_and_the_scenarios(morning):
    news("NHNN giữ nguyên lãi suất điều hành", "Lãi suất liên ngân hàng giảm")
    asyncio.run(daily.run(now=NOW + 3600))
    vn = next(r for r in shadow.rows() if r["factor"] == "VNINDEX" and r["horizon"] == "3d")
    o = vn["origin"]
    days = [realised.add_days(o, i) for i in range(0, 8)]
    down = {"VNINDEX": realised.Series("VNINDEX", "pct", [(d, 1000.0 - 20 * i) for i, d in enumerate(days)])}
    got = shadow.score(realised.add_days(o, 8), down)
    assert got["scored"] == 2  # VN-Index at 3 days and 1 week; the rest have no series yet
    s = report.summary()
    a3 = s["accuracy"]["3d"]
    assert a3["n"] == 1 and a3["uncalibrated"] is True and a3["by_segment"]["macro"]["n"] == 1
    row = next(r for r in shadow.rows() if r["factor"] == "VNINDEX" and r["horizon"] == "3d")
    assert row["realised"] == pytest.approx(-6.0)
    assert a3["direction_hit"] == (1.0 if row["expected"] < 0 else 0.0 if row["expected"] > 0 else None)
    vn_call = next(c for c in s["calls"]["3d"] if c["factor"] == "VNINDEX")
    assert vn_call["n"] == 1 and vn_call["right"] == int(row["call"] == "bán")
    assert s["runs"]["events"] == 1 and s["runs"]["drafts"] == 1 and s["days"] == [DAY]
    assert s["scenarios"] == {}  # one factor scored: too few to say which scenario the market took
    assert set(s["collection"]) >= {"items", "per_day", "by_segment", "by_region", "ingest_lag_min_p50"}


def test_the_trial_actor_acts_only_outside_a_request():
    assert roles.user(TRIAL_ACTOR)["role"] == "cio"

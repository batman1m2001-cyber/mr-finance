"""Urgent and important news (BRD-KPI-01, KPI-02; BRD_REMAINING_PLAN G6, G-D6): what the product proposes as urgent,
the CIO's flag and its 30 minutes; the independent reference, which of its stories are important, and how many we
collected."""

import asyncio
import time
from datetime import date, timedelta

import pytest
from operonx import Operon

from control import alerts, db
from events import store as events
from market import store as market
from news import reference, urgent
from news import store as news_store


def item(title, summary=""):
    return {"title": title, "summary": summary}


# -- urgent --------------------------------------------------------------------------------------


def test_an_sbv_rate_or_fx_band_decision_is_proposed_urgent_and_the_same_words_without_the_sbv_are_not():
    rate = urgent.proposals([], [item("NHNN điều chỉnh lãi suất điều hành, giảm 0,5 điểm")])
    band = urgent.proposals([], [item("Ngân hàng Nhà nước nới biên độ tỷ giá lên ±7%")])
    assert [p["id"] for p in rate] == ["sbv_rate"] and [p["id"] for p in band] == ["fx_band"]
    assert urgent.proposals([], [item("Ngân hàng thương mại tăng lãi suất huy động")]) == []
    assert urgent.proposals([], [item("Fed giữ lãi suất điều hành")]) == []  # not the SBV


def _vnindex(last_move_pct, days=300):
    """VN-Index: small alternating daily moves, then one day of ``last_move_pct``."""
    start = date(2025, 8, 1)
    level, pts = 1500.0, []
    for i in range(days):
        level *= 1 + (0.005 if i % 2 else -0.004)
        pts.append(((start + timedelta(days=i)).isoformat(), level))
    pts.append(((start + timedelta(days=days)).isoformat(), level * (1 + last_move_pct / 100)))
    market.put("VNINDEX", "test", "https://example.test", pts)
    return start + timedelta(days=days)


def test_a_move_past_three_deviations_of_the_daily_moves_is_proposed_and_a_normal_day_is_not():
    day = _vnindex(-6.0)
    at = time.mktime((day + timedelta(days=1)).timetuple())
    [p] = urgent.proposals(["VNINDEX"], [], at)
    assert p["kind"] == "move" and p["day"] == day.isoformat() and p["z"] < -3 and "VNINDEX" in p["reason"]
    _vnindex(0.5)
    assert urgent.proposals(["VNINDEX"], [], at) == []
    # stale data proposes nothing: the latest market day is weeks before the event
    assert urgent.proposals(["VNINDEX"], [], at + 30 * 86400) == []


def _event(title):
    ids = [r["id"] for r in news_store.add([_news(title)])[0]]
    return events.create(ids, None, "cio")


def _news(title, published=None, source="vneconomy_ck", n=[0]):
    from news import rules

    n[0] += 1
    published = time.time() - 600 if published is None else published
    return {
        "source": source,
        "outlet": "VnEconomy",
        "section": "Chứng khoán",
        "label": "Trong nước",
        "title": title,
        "summary": title,
        "url": f"https://vneconomy.vn/t{n[0]}.htm",
        "url_key": f"vneconomy.vn/t{n[0]}.htm",
        "title_key": rules.title_key(source, title),
        "published": published,
        "ingested": time.time(),
        "kind": "domestic",
        "status": "new",
        "relevance": "high",
        "event_type": None,
        "factors": ["VNINDEX"],
        "score": 1.0,
        "restricted": [],
        "held": 0,
    }


def test_the_cio_flags_an_event_urgent_with_a_reason_audited_and_can_take_it_off():
    from events.graph import event_urgent_flow

    ev = _event("NHNN điều chỉnh lãi suất điều hành")
    assert [p["id"] for p in ev["urgent_proposed"]] == ["sbv_rate"] and ev["urgent"] is None
    with pytest.raises(events.EventError, match="lý do"):
        events.set_urgent(ev["id"], True, " ", "cio")
    eng = Operon(event_urgent_flow, params={"event_id": None, "urgent": None, "reason": None, "by": None})
    refused = asyncio.run(eng.run(inputs={"event_id": ev["id"], "urgent": True, "reason": "x", "by": "rm"}))
    assert refused.get("$errors")  # only the CIO
    got = asyncio.run(eng.run(inputs={"event_id": ev["id"], "urgent": True, "reason": "Quyết định NHNN", "by": "cio"}))
    assert got["event"]["urgent"]["flag"] and got["event"]["urgent"]["reason"] == "Quyết định NHNN"
    assert events.set_urgent(ev["id"], False, "", "cio")["urgent"] is None
    with db.tx() as con:
        acts = [r[0] for r in con.execute("select action from audit_log where object = ?", (ev["id"],))]
    assert acts == ["event.create", "event.urgent", "event.urgent"]


def test_an_urgent_event_is_measured_against_thirty_minutes():
    from test_apply import MARKET, approved

    from measure import reports

    view, run = approved(*MARKET)
    events.set_urgent(view["event_id"], True, "Biến động lớn", "cio")
    sp = reports.speed()
    [row] = sp["runs"]
    assert row["urgent"] and row["urgent_met"] == (row["hours"] * 60 <= 30)
    [m] = sp["urgent"]["by_month"]
    assert m["minutes"]["n"] == 1 and sp["urgent"]["flagged"] == 1 and sp["urgent"]["target_minutes"] == 30


# -- important -----------------------------------------------------------------------------------


def _story(sid, title, articles, published):
    from email.utils import formatdate

    lis = "".join(
        f'<li><a href="https://news.google.com/x/{sid}{i}">{t}</a>&nbsp;&nbsp;<font color="#6f6f6f">{o}</font></li>'
        for i, (t, o) in enumerate(articles)
    )
    desc = f"<ol>{lis}</ol>".replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f"<item><title>{title} - {articles[0][1]}</title><link>https://news.google.com/x/{sid}</link>"
        f"<guid>{sid}</guid><pubDate>{formatdate(published)}</pubDate><description>{desc}</description></item>"
    )


def feed(*stories):
    return "<rss><channel>" + "".join(stories) + "</channel></rss>"


def test_important_is_on_our_topics_from_two_outlets_and_collected_is_judged_once_a_day_later():
    now = time.time()
    t = now - 3600
    news_store.add([_news("Chủ tịch Fed từ chối phát tín hiệu về đường đi của lãi suất", t)])
    xml = feed(
        # on our topics (lãi suất, Fed), two outlets, and we have it: collected
        _story("a", "Chủ tịch Fed bất ngờ phát tín hiệu về lãi suất, thị trường phản ứng",
               [("Chủ tịch Fed bất ngờ phát tín hiệu về lãi suất", "Báo Dân trí"), ("Fed và lãi suất", "CafeF")], t),
        # on our topics, three outlets, we do not have it: missed (CafeF is an outlet we follow)
        _story("b", "Giá vàng miếng SJC lập đỉnh mới", [("Giá vàng miếng SJC lập đỉnh", "CafeF"),
               ("Vàng SJC tăng", "Laodong.vn"), ("SJC lên đỉnh", "VTV.vn")], t),
        # one outlet only: not important
        _story("c", "Tỷ giá USD hôm nay tăng", [("Tỷ giá USD hôm nay tăng", "Laodong.vn")], t),
        # two outlets, off our topics: not important
        _story("d", "Ô tô bay ra mắt", [("Ô tô bay ra mắt", "Kenh14.vn"), ("Xe bay", "Tuổi Trẻ")], t),
    )  # fmt: skip
    assert reference.keep(reference.parse(xml), now) == {"added": 4, "grown": 0}
    assert reference.judge(now) == 0  # nothing is judged before a day has passed
    assert reference.judge(now + 25 * 3600) == 4
    c = reference.coverage()
    [day] = c["by_day"]
    assert (day["important"], day["collected"], day["share"]) == (2, 1, 0.5)
    assert day["followed"] == 2 and day["followed_share"] == 0.5  # CafeF carried both
    [miss] = c["misses"]
    assert miss["title"] == "Giá vàng miếng SJC lập đỉnh mới" and miss["followed"]
    # judged once: the story coming back with more outlets changes nothing
    assert reference.keep(reference.parse(xml), now + 26 * 3600) == {"added": 0, "grown": 0}


def test_a_story_seen_again_grows_its_outlets_until_it_is_judged():
    now = time.time()
    one = feed(_story("e", "Giá dầu Brent giảm mạnh", [("Giá dầu Brent giảm mạnh", "CafeF")], now))
    two = feed(_story("e", "Giá dầu Brent giảm mạnh", [("Giá dầu Brent giảm mạnh", "CafeF"),
               ("Dầu Brent giảm", "VnExpress")], now))  # fmt: skip
    reference.keep(reference.parse(one), now)
    assert reference.keep(reference.parse(two), now + 7200) == {"added": 0, "grown": 1}
    reference.judge(now + 25 * 3600)
    assert reference.coverage()["by_day"][0]["important"] == 1


def test_the_reference_job_reads_keeps_and_alerts_when_the_reference_cannot_be_read():
    from news.graph import reference_flow

    eng = Operon(reference_flow, params={"feed": None, "now": None, "tick": None, "at": None})
    got = asyncio.run(eng.run(inputs={"feed": feed(_story("f", "VN-Index giảm", [("VN-Index giảm", "CafeF")], 0))}))
    assert got["error"] is None and got["added"] == 1
    bad = asyncio.run(eng.run(inputs={"feed": "<html>not a feed"}))
    assert bad["error"] and alerts.is_open("news_feed", "reference")
    asyncio.run(eng.run(inputs={"feed": feed()}))
    assert not alerts.is_open("news_feed", "reference")

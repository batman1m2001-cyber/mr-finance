"""The schedules the BRD sets (BRD-FR-101 and RULE-WF-01: the news every 10 minutes; NFR-02's 10-minute news to
inbox rests on it), read from the application as it is served, and what each scheduled run does."""

from operonx.app import Application
from test_views import INGEST, NOW, ok

from app import web
from news import store as news_store


def jobs():
    Application.find(".")  # app/main.py declares the jobs and fills web.JOBS
    return {j["id"]: j for j in web.JOBS}


def test_the_news_is_fetched_every_10_minutes_and_the_other_brd_cadences():
    j = jobs()
    assert j["news_ingest"]["when"] == {"every": "10m"}  # FR-101, WF-01
    assert j["agent_worker"]["when"]["every"] in ("5s", "10s")  # a queued run starts at once (AI-13)
    assert j["inbox_import"]["when"] == {"every": "10m"}  # the AI zone's packages, same cadence as the news
    assert j["audit_check"]["when"] == {"every": "1h"}  # NFR-12
    assert j["heartbeat"]["when"] == {"every": "20s"}  # NFR-03: three beats a minute


def test_each_scheduled_run_reads_every_source_and_one_broken_feed_stops_none_of_the_others():
    from news.ops import config

    sources = [s["id"] for s in config()["sources"]]
    feeds = {s: "<rss version='2.0'><channel></channel></rss>" for s in sources}
    feeds[sources[0]] = "<rss><không phải xml"
    ok(INGEST, feeds=feeds, now=NOW)
    run = news_store.last_run()
    assert set(run["sources"]) == set(sources)
    assert run["sources"][sources[0]]["error"] and all(not run["sources"][s].get("error") for s in sources[1:])

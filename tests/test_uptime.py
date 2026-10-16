"""Availability in business hours (BRD-NFR-03, BRD_REMAINING_PLAN G5): the heartbeat, the business-minute
arithmetic, outages, the alert below 99.5 %, and where it is shown."""

import asyncio
from datetime import datetime

from operonx import Operon

from control import alerts, db, uptime

TZ = uptime.TZ


def at(y, mo, d, h, mi, s=0):
    return datetime(y, mo, d, h, mi, tzinfo=TZ).timestamp() + s


MON = (2026, 10, 12)  # a Monday


def fill(start, end, gaps=()):
    """A beat in every business minute of [start, end) except those in ``gaps`` ((from, to) epoch seconds)."""
    minutes = uptime.business_minutes(int(start // 60), int(end // 60))
    skip = {m for a, b in gaps for m in range(int(a // 60), int(b // 60))}
    with db.tx() as con:
        con.executemany(
            "insert or ignore into heartbeats values (?, ?, 1)", [(m, m * 60 + 5.0) for m in minutes if m not in skip]
        )
    return len(minutes)


def test_business_minutes_are_weekdays_from_eight_to_half_past_five_vietnam_time():
    assert uptime.business(int(at(*MON, 8, 0) // 60)) and uptime.business(int(at(*MON, 17, 29) // 60))
    assert not uptime.business(int(at(*MON, 7, 59) // 60)) and not uptime.business(int(at(*MON, 17, 30) // 60))
    assert not uptime.business(int(at(2026, 10, 17, 10, 0) // 60))  # Saturday
    week = uptime.business_minutes(int(at(*MON, 0, 0) // 60), int(at(2026, 10, 19, 0, 0) // 60))
    assert len(week) == 5 * (9 * 60 + 30)


def test_a_beat_late_in_its_minute_or_twice_in_it_is_one_minute():
    first = uptime.beat(now=at(*MON, 9, 0, 59.5))
    again = uptime.beat(now=at(*MON, 9, 0, 59.9))
    assert first["new"] and not again["new"] and first["business"]
    with db.tx() as con:
        assert con.execute("select count(*) from heartbeats").fetchone()[0] == 1


def test_availability_counts_business_minutes_from_the_first_beat_to_now_and_lists_outages():
    start, now = at(*MON, 8, 0), at(2026, 10, 16, 18, 0)  # Monday morning to Friday evening
    expected = fill(start, now, gaps=[(at(2026, 10, 14, 10, 0), at(2026, 10, 14, 10, 10))])
    got = uptime.month("2026-10", now=now)
    assert got["business_minutes"] == expected == 2850 and got["down_minutes"] == 10
    assert got["availability"] == round(2840 / 2850, 5) and got["met"]  # 99.65 %
    assert got["outages"] == [{"from": at(2026, 10, 14, 10, 0), "to": at(2026, 10, 14, 10, 10), "minutes": 10}]
    assert got["since"] == start  # nothing is claimed before the first beat
    # the current minute is not counted yet, nor anything after it
    mid = uptime.measure(start, now, now=at(*MON, 10, 5, 30))
    assert mid["business_minutes"] == 125 and mid["down_minutes"] == 0


def test_a_night_and_a_weekend_without_beats_are_not_downtime_but_a_restart_in_hours_is():
    fill(at(*MON, 8, 0), at(*MON, 17, 30))
    fill(at(2026, 10, 13, 8, 0), at(2026, 10, 13, 17, 30), gaps=[(at(2026, 10, 13, 14, 0), at(2026, 10, 13, 14, 2))])
    got = uptime.measure(at(*MON, 0, 0), at(2026, 10, 14, 0, 0), now=at(2026, 10, 14, 12, 0))
    assert got["business_minutes"] == 2 * 570 and got["down_minutes"] == 2 and len(got["outages"]) == 1


def test_below_the_target_admin_is_alerted_once_and_it_resolves_when_back_above():
    now = at(2026, 10, 16, 18, 0)
    fill(at(*MON, 8, 0), now, gaps=[(at(2026, 10, 14, 10, 0), at(2026, 10, 14, 10, 30))])  # 30 minutes down
    got = uptime.check(now=now)
    assert not got["met"] and got["availability"] < 0.995
    uptime.check(now=now)
    [a] = alerts.for_role("admin")
    assert a["kind"] == "availability" and a["key"] == "2026-10" and a["count"] == 1 and a["severity"] == "high"
    assert alerts.for_role("cio") == []
    fill(at(2026, 10, 14, 10, 0), at(2026, 10, 14, 10, 30))  # (the measure is recomputed: say the beats were found)
    assert uptime.check(now=now)["met"] and not alerts.is_open("availability", "2026-10")


def test_the_heartbeat_job_records_the_minute_and_the_pages_show_the_measure():
    from starlette.testclient import TestClient

    from control.graph import heartbeat_flow

    out = asyncio.run(Operon(heartbeat_flow, params={"tick": None, "at": None}).run(inputs={}))
    assert out["beat"]["new"]
    with db.tx() as con:
        assert con.execute("select count(*) from heartbeats").fetchone()[0] == 1
    from operonx.app import Application

    with TestClient(Application.find(".").asgi()) as c:
        a = c.get("/api/measure").json()["availability"]
        assert a["target"] == 0.995 and a["since"] is not None
        assert c.get("/api/system").json()["availability"]["target"] == 0.995

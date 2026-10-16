"""Availability in business hours (BRD-NFR-03 “99,5% trong giờ làm việc”; BRD_REMAINING_PLAN G5, G-D5).

- **Heartbeat.** The ``heartbeat`` job beats every 20 seconds inside the server (``operonx serve``): each beat writes
  its minute to ``heartbeats`` in the state database. A minute is up when it has a beat: the server process was
  running, its scheduler was ticking and it could write its database. Three beats a minute, so a beat late by a
  few seconds does not lose a minute that was up.
- **Business minutes.** Monday to Friday, 08:00–17:30, Vietnam time (``Asia/Ho_Chi_Minh``). Public holidays are
  not taken out: the BRD names none, so they count as business minutes (a stricter measure, never a kinder one).
- **Availability** = business minutes with a beat ÷ business minutes, from the first beat ever (nothing is claimed
  for before it) to the current minute. A restart for a deploy counts as down, as does anything that stops the
  process or its database writes. Each run of missing business minutes is an outage, listed.
- **Alert.** Below 99,5 % for the month so far, an ``availability`` alert for Admin; back at or above, resolved.
  Checked once a minute, on the minute's first beat.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from control import db

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
OPEN, CLOSE = 8 * 60, 17 * 60 + 30  # minutes after local midnight
TARGET = 0.995


def business(minute: int) -> bool:
    """Whether a minute (minutes since the epoch) is a business minute."""
    t = datetime.fromtimestamp(minute * 60, TZ)
    return t.weekday() < 5 and OPEN <= t.hour * 60 + t.minute < CLOSE


def beat(now: Optional[float] = None) -> Dict[str, Any]:
    """One heartbeat: its minute recorded (once). ``new`` is whether it was the minute's first."""
    now = time.time() if now is None else now
    minute = int(now // 60)
    with db.tx() as con:
        cur = con.execute("insert or ignore into heartbeats values (?, ?, ?)", (minute, now, int(business(minute))))
        new = cur.rowcount == 1
    return {"minute": minute, "business": business(minute), "new": new}


def _local_midnight(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=TZ).timestamp() // 60)


def business_minutes(start: int, end: int) -> List[int]:
    """Every business minute in ``[start, end)`` (minutes since the epoch), in order."""
    out: List[int] = []
    if end <= start:
        return out
    day = datetime.fromtimestamp(start * 60, TZ).date()
    last = datetime.fromtimestamp((end - 1) * 60, TZ).date()
    while day <= last:
        if day.weekday() < 5:
            base = _local_midnight(day)
            out.extend(range(max(start, base + OPEN), min(end, base + CLOSE)))
        day += timedelta(days=1)
    return out


def measure(start: float, end: float, now: Optional[float] = None) -> Dict[str, Any]:
    """Availability over ``[start, end)`` (epoch seconds), cut to the first beat and to the current minute."""
    now = time.time() if now is None else now
    with db.tx() as con:
        first = con.execute("select min(minute) from heartbeats").fetchone()[0]
        if first is None:
            return {"measured": False, "target": TARGET}
        s, e = max(int(start // 60), first), min(int(end // 60), int(now // 60))
        have = {
            r[0]
            for r in con.execute(
                "select minute from heartbeats where business = 1 and minute >= ? and minute < ?", (s, e)
            )
        }
    expected = business_minutes(s, e)
    missing = [m for m in expected if m not in have]
    outages: List[Dict[str, Any]] = []
    for m in missing:
        if outages and outages[-1]["_end"] == m:
            outages[-1]["_end"] = m + 1
        else:
            outages.append({"_start": m, "_end": m + 1})
    shown = [{"from": o["_start"] * 60, "to": o["_end"] * 60, "minutes": o["_end"] - o["_start"]} for o in outages]
    share = (len(expected) - len(missing)) / len(expected) if expected else None
    return {
        "measured": True,
        "since": first * 60,
        "from": s * 60,
        "to": max(e, s) * 60,
        "business_minutes": len(expected),
        "up_minutes": len(expected) - len(missing),
        "down_minutes": len(missing),
        "availability": round(share, 5) if share is not None else None,
        "target": TARGET,
        "met": share is None or share >= TARGET,
        "outages": shown,
    }


def _month_bounds(ym: str) -> tuple:
    y, m = (int(x) for x in ym.split("-"))
    start = datetime(y, m, 1, tzinfo=TZ)
    end = datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=TZ)
    return start.timestamp(), end.timestamp()


def month(ym: Optional[str] = None, now: Optional[float] = None) -> Dict[str, Any]:
    """One calendar month (Vietnam time); the current one by default."""
    now = time.time() if now is None else now
    ym = ym or datetime.fromtimestamp(now, TZ).strftime("%Y-%m")
    return {"month": ym, **measure(*_month_bounds(ym), now=now)}


def by_month(now: Optional[float] = None) -> Dict[str, Any]:
    """Every month from the first beat to now, newest first (the monthly report, Hệ thống)."""
    now = time.time() if now is None else now
    with db.tx() as con:
        first = con.execute("select min(minute) from heartbeats").fetchone()[0]
    if first is None:
        return {"months": [], "target": TARGET, "since": None}
    months, d = [], datetime.fromtimestamp(first * 60, TZ).replace(day=1)
    stop = datetime.fromtimestamp(now, TZ)
    while (d.year, d.month) <= (stop.year, stop.month):
        months.append(month(d.strftime("%Y-%m"), now=now))
        d = d.replace(year=d.year + (d.month == 12), month=d.month % 12 + 1)
    return {"months": months[::-1], "target": TARGET, "since": first * 60}


def check(now: Optional[float] = None) -> Dict[str, Any]:
    """The month so far against the target: an alert for Admin below it, resolved at or above it."""
    from control import alerts

    got = month(now=now)
    if not got.get("measured") or got["availability"] is None:
        return got
    pct = f"{got['availability'] * 100:.2f}".replace(".", ",")
    if not got["met"] and not alerts.is_open("availability", got["month"]):
        alerts.raise_(
            "availability",
            got["month"],
            f"Sẵn sàng tháng {got['month']}: {pct}% (mục tiêu 99,5%)",
            f"{got['down_minutes']} phút giờ làm việc không có nhịp, {len(got['outages'])} lần gián đoạn",
        )
    elif got["met"]:
        alerts.resolve("availability", got["month"], f"Sẵn sàng tháng {got['month']}: {pct}%")
    return got

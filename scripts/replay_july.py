"""The 3-month replay (BUSINESS_FEEDBACK_1021_PLAN B1.5): July 2026's news played back morning by morning through the
trial's own steps, and every draft's shadow forecasts scored against what the market did by now.

    uv run python scripts/replay_july.py [--first 2026-07-01] [--last 2026-07-20] [--per-day 2] [--fetch-only]

- **The news** of the whitelisted outlets (VnEconomy, VnExpress, CafeF, Vietstock), from Google News search by
  outlet and day — titles and times only, as the outlets' own feeds have long rotated July out; each window
  through the same gates as the live feeds, as if fetched when it ended. Cached in out/replay/feeds (fetched once).
- **Each weekday morning at 08:30**: the news of the 24 hours before it, grouped by the CIO model into ``--per-day``
  events (``trial.daily.group``), the CIO agent and the challenger on each (``cio_agent_flow``), the shadow forecasts
  kept from the close before that morning (``trial.shadow``).
- **Fair**: the models' knowledge ends around June 2026 (they say so, and know no July–September outcome: the probe
  in the plan), and what the agents read holds no market level, only the event's news and the factor catalogue.
  Claude Code tells the model today's date; nothing else of October reaches it.
- **Apart from the demo**: everything happens in its own state file, out/replay/state.db (a copy of the live one's
  market data and configuration); the report is out/trial/replay.json, which /api/trial shows.

Resumable: a morning already played is skipped. A first read, not proof: 20–30 events in three weeks of one summer.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "replay"
FEEDS = OUT / "feeds"
STATE = OUT / "state.db"
REPORT = ROOT / "out" / "trial" / "replay.json"
# the outlet's site, the live feed id its news goes in as (the gates and the segments read the source)
SITES = {"vneconomy.vn": "vneconomy_tc", "vnexpress.net": "vnexpress_kd", "cafef.vn": "cafef_ck",
         "vietstock.vn": "vietstock_vm"}
WINDOW_DAYS = 1
MORNING = (8, 30)
GOOGLE = "https://news.google.com/rss/search?"


def env() -> None:
    """The deployment's .env (the agents' endpoint and models), the replay's own state file."""
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)
    os.environ["MF_STATE"] = str(STATE)
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]


def windows(first: date, last: date):
    d = first
    while d <= last:
        yield d, min(d + timedelta(days=WINDOW_DAYS), last + timedelta(days=1))
        d += timedelta(days=WINDOW_DAYS)


def fetch(first: date, last: date) -> int:
    """Every outlet's news per window from Google News search, kept as the RSS it came as (once)."""
    FEEDS.mkdir(parents=True, exist_ok=True)
    n = 0
    for site in SITES:
        for a, b in windows(first - timedelta(days=1), last):
            path = FEEDS / f"{site}_{a}.xml"
            if not path.exists():
                q = f"site:{site} after:{a - timedelta(days=1)} before:{b}"
                url = GOOGLE + urllib.parse.urlencode({"q": q, "hl": "vi", "gl": "VN", "ceid": "VN:vi"})
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                path.write_bytes(urllib.request.urlopen(req, timeout=30).read())
                time.sleep(1.5)  # gently: one outlet-window at a time
            n += len(ET.fromstring(path.read_bytes()).findall("./channel/item"))
    return n


def as_feed(raw: bytes, site: str, a: date, b: date) -> tuple[str, float]:
    """The window's items as a plain RSS feed (the outlet's name off the title), and when it is read: its end. The
    gates take only the outlet's own links and the article sits behind Google's redirect, so each link is the
    outlet's home page with Google's id in the query (in the replay's state only)."""
    items = []
    for it in ET.fromstring(raw).findall("./channel/item"):
        when = parsedate_to_datetime(it.findtext("pubDate"))
        if not (a <= when.astimezone().date() < b):
            continue
        title = (it.findtext("title") or "").rsplit(" - ", 1)[0].strip()
        gid = hashlib.sha1((it.findtext("link") or title).encode()).hexdigest()[:16]
        link = f"https://{site}/?gn={gid}"
        esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")  # noqa: E731
        items.append(f"<item><title>{esc(title)}</title><link>{esc(link)}</link><description>{esc(title)}"
                     f"</description><pubDate>{format_datetime(when)}</pubDate></item>")
    end = datetime.combine(b, datetime.min.time()).timestamp() - 60
    return f"<rss version='2.0'><channel>{''.join(items)}</channel></rss>", end


def prepare() -> None:
    """The replay's own state: the live one's copy (market data, configuration, staff), without its trial."""
    if STATE.exists():
        return
    OUT.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(f"file:{ROOT / 'data' / 'state.db'}?mode=ro", uri=True)
    dst = sqlite3.connect(STATE)
    src.backup(dst)
    src.close()
    for t in ("trial_events", "shadow_forecasts"):
        dst.execute(f"delete from {t}")
    dst.commit()
    dst.close()


def ingest(first: date, last: date) -> dict:
    from operonx import Operon

    from news.graph import ingest_flow

    engine = Operon(ingest_flow, params={"feeds": None, "now": None, "tick": None, "at": None})
    total = {"added": 0, "refused": 0, "duplicates": 0}
    for a, b in windows(first - timedelta(days=1), last):
        for site, source in SITES.items():
            xml, end = as_feed((FEEDS / f"{site}_{a}.xml").read_bytes(), site, a, b)
            out = asyncio.run(engine.run(inputs={"feeds": {source: xml}, "now": end}))
            got = (out.get("ingest") or {})
            for k in total:
                total[k] += int(got.get(k) or 0)
    return total


async def play(day: date, per_day: int) -> list:
    """One July morning through the trial's own steps."""
    from control.roles import TRIAL_ACTOR
    from events import store as events
    from news import store as news_store
    from trial import daily, segments, shadow
    from views import store as vstore

    now = datetime.combine(day, datetime.min.time()).replace(hour=MORNING[0], minute=MORNING[1]).timestamp()
    news = daily.candidates(now, since=now - daily.WINDOW_S)
    if not news:
        return []
    t0 = time.time()
    grouped = await daily.group(news, per_day)
    made = []
    for e in grouped["events"]:
        items = news_store.get(e["news_ids"])
        ev = events.create(e["news_ids"], e["title"], by=TRIAL_ACTOR)
        trial = {
            "created": now,
            "replay": True,
            "origin": (day - timedelta(days=1)).isoformat(),
            "title": e["title"],
            "why": e["why"],
            "news_ids": e["news_ids"],
            "segment": e["segment"] or segments.of_items(items),
            "segment_by": "agent" if e["segment"] else "news",
            "region": segments.region(items),
            "first_published": min((i.get("published") or i["ingested"]) for i in items),
            "candidates": len(news),
            "group_s": round(time.time() - t0, 1),
            "group_tokens": (grouped["meta"].get("tokens_in") or 0) + (grouped["meta"].get("tokens_out") or 0),
        }
        daily._keep(ev["id"], day.isoformat(), trial)
        t1 = time.time()
        got = await daily.run_agent(ev["id"])
        v = vstore.get(got["view_id"]) if got["view_id"] else None
        trial.update(view_id=got["view_id"], agent_s=round(time.time() - t1, 1), status=(v or {}).get("status"))
        trial["error"] = got["error"] or (v or {}).get("challenge_error")
        if v and v["status"] in shadow.RECORDED:
            trial["forecasts"] = shadow.record(v, trial)
        daily._keep(ev["id"], day.isoformat(), trial)
        made.append(f"{ev['id']} {trial['segment']} {trial['status']} {trial['agent_s']} s · {e['title'][:70]}")
    return made


async def play_all(first: date, last: date, per_day: int, done: set) -> None:
    """Every weekday morning not played yet, in one event loop (the model clients are kept for the loop)."""
    d = first
    while d <= last:
        if d.weekday() < 5 and d.isoformat() not in done:
            for line in await play(d, per_day):
                print(d, line, flush=True)
        d += timedelta(days=1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--first", default="2026-07-01")
    ap.add_argument("--last", default="2026-07-20")
    ap.add_argument("--per-day", type=int, default=2)
    ap.add_argument("--fetch-only", action="store_true")
    a = ap.parse_args()
    first, last = date.fromisoformat(a.first), date.fromisoformat(a.last)
    print("fetched", fetch(first, last), "items")
    if a.fetch_only:
        return 0
    prepare()
    env()
    from operonx.core.registry.resource_hub import ResourceHub

    ResourceHub.set_instance(ResourceHub.from_yaml(str(ROOT / "resources.yaml")))
    from trial import daily, report, shadow

    print("ingest", ingest(first, last))  # again on a re-run: what is already in comes back as duplicates
    asyncio.run(play_all(first, last, a.per_day, set(daily.days())))
    print("score", shadow.score())
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({**report.summary(), "replay": {"first": a.first, "last": a.last,
                                                                 "per_day": a.per_day}}, ensure_ascii=False))
    print("report", REPORT)
    return 0


if __name__ == "__main__":
    sys.exit(main())

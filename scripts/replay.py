"""The replay (BUSINESS_FEEDBACK_1021_PLAN B1.5, REPLAY_PLAN): past news played back morning by morning through the
trial's own steps, every draft's shadow forecasts scored against what the market did by now, and the trial's View B
(AGENT_EVALUATION_PLAN: precision, recall, simulated VND, cost) measured on it.

    uv run python scripts/replay.py --name 2026-09 --first 2026-09-22 --last 2026-10-21 [--per-day 5]
    uv run python scripts/replay.py --name 2026-07 --score-only        # score again, no model call

- **The news** of the whitelisted outlets (VnEconomy, VnExpress, CafeF, Vietstock), from Google News search by
  outlet and day — titles and times only, as the outlets' own feeds have long rotated them out; each window
  through the same gates as the live feeds, as if fetched when it ended. Cached in out/replay/feeds (fetched once).
- **Each morning at 08:30** (every day, as the live trial runs; ``--weekdays`` for the July replay's shape): the
  news since the morning before (at most 36 h, the live rule), grouped by the CIO model into ``--per-day`` events
  (``trial.daily.group``), the CIO agent and the challenger on each (``cio_agent_flow``), the shadow forecasts kept
  from the close before that morning (``trial.shadow``). Nobody approves: approval changes no score.
- **Fair**: the models' knowledge ends around June 2026 (they say so, and know no later outcome: the probe in the
  plan), and what the agents read holds no market level, only the event's news and the factor catalogue. Claude
  Code tells the model today's date; nothing else of the outcome reaches it.
- **The book**: today's families' holdings frozen once per morning played (``finance.keep(late=True)``): the VND
  says what following the calls would have done to the books as they stand now, labelled late like any late
  snapshot (the holdings of a past morning were never kept).
- **Scored as live** (``evaluate.score``), over the mornings played only; the market data copied from the live
  state first. Event recall is not measured: the reference source began on 08/10 and matches the live items.
- **Apart from the demo**: everything happens in its own state file, out/replay/<name>/state.db (a copy of the
  live one's market data, configuration and families, without its news or its trial); the report is
  out/trial/replays/<name>.json (``/api/trial/replay/<name>``), each move's drill-down beside it.

Resumable: a morning already played is skipped; its events stopped by the day's token budget run again.
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
REPORTS = ROOT / "out" / "trial" / "replays"
LIVE = ROOT / "data" / "state.db"
# the outlet's site, the live feed id its news goes in as (the gates and the segments read the source)
SITES = {"vneconomy.vn": "vneconomy_tc", "vnexpress.net": "vnexpress_kd", "cafef.vn": "cafef_ck",
         "vietstock.vn": "vietstock_vm"}
WINDOW_DAYS = 1
MORNING = (8, 30)
GOOGLE = "https://news.google.com/rss/search?"


def env(state: Path, first: date, last: date) -> None:
    """The deployment's .env (the agents' endpoint and models), the replay's own state file, its last morning."""
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)
    # the day's token budget counts from today's midnight, and the replay plays many mornings today: each morning
    # played gets the live day's budget (the 2026-09 run stopped on 04/10 at 3,000,000)
    daily = int(os.environ.get("AGENT_DAILY_TOKENS") or 300_000)
    os.environ["AGENT_DAILY_TOKENS"] = str(daily * ((last - first).days + 1))
    os.environ["MF_STATE"] = str(state)
    os.environ["MF_TRIAL_UNTIL"] = last.isoformat()  # the mornings scored end with the last one played
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


FRESH = ("trial_events", "trial_days", "shadow_forecasts", "eval_scores", "eval_snapshots", "call_costs",
         "news_items", "news_runs", "reference_stories")


def prepare(state: Path) -> None:
    """The replay's own state: the live one's copy (market data, configuration, staff, families), without its news
    and its trial (the replay's news are only the ones it plays back)."""
    if state.exists():
        return
    state.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(f"file:{LIVE}?mode=ro", uri=True)
    dst = sqlite3.connect(state)
    src.backup(dst)
    src.close()
    for t in FRESH:
        dst.execute(f"delete from {t}")
    dst.commit()
    dst.close()


def refresh_market(state: Path) -> int:
    """The live state's market data copied in, so the moves are scored against what the market did by now."""
    con = sqlite3.connect(f"file:{state}", uri=True)  # a URI connection, to attach the live one read-only
    con.execute("attach database ? as live", (f"file:{LIVE}?mode=ro",))
    con.execute("delete from main.market_series")
    con.execute("insert into main.market_series select * from live.market_series")
    n = con.execute("select count(*) from main.market_series").fetchone()[0]
    con.commit()
    con.close()
    return n


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
    """One past morning through the trial's own steps."""
    from control.roles import TRIAL_ACTOR
    from events import store as events
    from news import store as news_store
    from trial import daily, segments, shadow
    from views import store as vstore

    now = datetime.combine(day, datetime.min.time()).replace(hour=MORNING[0], minute=MORNING[1]).timestamp()
    news = daily.candidates(now)  # since the morning played before, at most 36 h (the live rule)
    if not news:
        daily.note_day(day.isoformat(), status="no_news", at=now, candidates=0)
        return []
    t0 = time.time()
    daily.note_day(day.isoformat(), status="running", started=now, candidates=len(news), error=None)
    grouped = await daily.group(news, per_day)
    daily.note_day(day.isoformat(), group={**grouped["meta"], "s": round(time.time() - t0, 1)},
                   events=len(grouped["events"]))
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
    drafts = sum(1 for t in daily.days().get(day.isoformat(), []) if t.get("view_id"))
    daily.note_day(day.isoformat(), status="ran" if drafts else "no_drafts", finished=now, drafts=drafts)
    return made


BUDGET = "Vượt ngân sách token trong ngày"


async def retry_budget() -> list:
    """The events of mornings already played whose agent stopped on the day's token budget, run again: the budget
    is the live day's, and a replay plays many mornings in one (an agent's own error stays as it is)."""
    from trial import daily, shadow
    from views import store as vstore

    made = []
    for day, rows in sorted(daily.days().items()):
        for t in rows:
            v = vstore.get(t["view_id"]) if t.get("view_id") else None
            if not v or v["status"] != "AGENT_ERROR" or BUDGET not in str(v.get("error")):
                continue
            t1 = time.time()
            got = await daily.run_agent(t["event_id"])
            v = vstore.get(got["view_id"]) if got["view_id"] else None
            t.update(view_id=got["view_id"], agent_s=round(time.time() - t1, 1), status=(v or {}).get("status"))
            t["error"] = got["error"] or (v or {}).get("challenge_error")
            if v and v["status"] in shadow.RECORDED:
                t["forecasts"] = shadow.record(v, t)
            data = {k: x for k, x in t.items() if k not in ("event_id", "day")}
            daily._keep(t["event_id"], day, data)
            made.append(f"{day} {t['event_id']} again {t['status']} {t['agent_s']} s · {t['title'][:70]}")
        drafts = sum(1 for t in daily.days().get(day, []) if t.get("view_id"))
        if made and made[-1].startswith(day):
            daily.note_day(day, status="ran" if drafts else "no_drafts", drafts=drafts)
    return made


async def play_all(first: date, last: date, per_day: int, done: set, weekdays: bool) -> None:
    """Every morning not played yet, in one event loop (the model clients are kept for the loop); first the events
    stopped by the token budget."""
    for line in await retry_budget():
        print(line, flush=True)
    d = first
    while d <= last:
        if (d.weekday() < 5 or not weekdays) and d.isoformat() not in done:
            for line in await play(d, per_day):
                print(d, line, flush=True)
        d += timedelta(days=1)


async def measure(name: str, meta: dict) -> dict:
    """View B on the replay: the mornings played kept on today's book, every move scored as live, the report and
    each move's drill-down written. A day not played is no morning of the replay (the July one skipped weekends)."""
    from trial import costs, daily, evaluate, finance, report, shadow

    played = sorted(daily.notes().keys() | daily.days().keys())
    every = evaluate.mornings
    evaluate.mornings = lambda today: [m for m in every(today) if m["day"] in played]
    for day in played:
        await finance.keep(day, late=True)
    print("shadow", shadow.score())
    print("score", evaluate.score())
    acc = evaluate.summary()
    acc["event_recall"] = None  # not measured: the reference source began on 08/10 and matches the live items
    c = costs.summary()
    out = {
        "replay": {**meta, "name": name, "at": time.time(), "mornings": len(played)},
        "evaluation": {
            "accuracy": acc,
            "finance": finance.summary(),
            "costs": {"agents": c["agents"], "total": c["total"]},
            "moves": evaluate.moves(),
        },
        "legacy": report.summary(),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(json.dumps(out, ensure_ascii=False))
    details = {m["id"]: evaluate.detail(m["id"]) for m in out["evaluation"]["moves"]}
    (REPORTS / f"{name}.moves.json").write_text(json.dumps(details, ensure_ascii=False))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--name", required=True, help="the replay's folder and report name, e.g. 2026-09")
    ap.add_argument("--first")
    ap.add_argument("--last")
    ap.add_argument("--per-day", type=int, default=5)
    ap.add_argument("--weekdays", action="store_true", help="weekday mornings only (the July replay)")
    ap.add_argument("--fetch-only", action="store_true")
    ap.add_argument("--score-only", action="store_true", help="no news, no model call: score and report again")
    a = ap.parse_args()
    state = OUT / a.name / "state.db"
    meta_path = state.parent / "replay.json"  # the run's own dates, so --score-only needs none
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    meta.update({k: v for k, v in (("first", a.first), ("last", a.last)) if v})
    meta.setdefault("per_day", a.per_day)
    meta.setdefault("weekdays", a.weekdays)
    first, last = date.fromisoformat(meta["first"]), date.fromisoformat(meta["last"])
    if not a.score_only:
        print("fetched", fetch(first, last), "items")
        if a.fetch_only:
            return 0
    prepare(state)
    meta_path.write_text(json.dumps(meta))
    env(state, first, last)
    from operonx.core.registry.resource_hub import ResourceHub

    ResourceHub.set_instance(ResourceHub.from_yaml(str(ROOT / "resources.yaml")))
    from trial import daily

    if not a.score_only:
        print("ingest", ingest(first, last))  # again on a re-run: what is already in comes back as duplicates
        asyncio.run(play_all(first, last, meta["per_day"], set(daily.days()), meta["weekdays"]))
    print("market", refresh_market(state), "rows")
    out = asyncio.run(measure(a.name, meta))
    b = out["evaluation"]["accuracy"]["horizons"]
    for h, x in b.items():
        print(h, "precision", x["precision"], "recall", x["recall"])
    print("report", REPORTS / f"{a.name}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())

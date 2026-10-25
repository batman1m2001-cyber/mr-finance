"""The morning desk over a replay's mornings (FORECAST_DESK_PLAN step 5): each morning's packet, the desk's call
(the CIO's model through the deployment's endpoint), its forecasts kept as a track the lab scores.

    uv run python scripts/forecast_desk.py --replay 2026-07 --tag desk1 [--sources odds,kb,record]
    uv run python scripts/forecast_lab.py --set dev --track desk1

Writes out/lab/tracks/<tag>/<replay>.json (the lab's track) and out/lab/desk/<tag>/<replay>/<morning>.json (the
packet, the reply, the tokens). Resumable: a morning already answered is kept. ``--after`` names the replays played
before this one: their desk calls and the agents' join the record (only moves over by each origin).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import pickle
import shutil
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAB = ROOT / "out" / "lab"
sys.path[:0] = [str(ROOT / "scripts")]


def env(state: Path) -> None:
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k, v)
    os.environ["AGENT_DAILY_TOKENS"] = "100000000"  # the desk is measured, not budgeted: its tokens are counted
    os.environ["MF_STATE"] = str(state)
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]


def read(state: Path):
    """The replay's mornings: events by day, the drafts' shadow forecasts, the views."""
    con = sqlite3.connect(f"file:{state}?mode=ro", uri=True)
    events: dict = {}
    for eid, day, data in con.execute("select event_id, day, data from trial_events order by day, created"):
        events.setdefault(day, []).append({**json.loads(data), "event_id": eid})
    shadows = [{"view_id": v, "factor": f, "horizon": h, **json.loads(d)}
               for v, f, h, d in con.execute("select view_id, factor, horizon, data from shadow_forecasts")]
    views = {i: json.loads(d) | {"id": i} for i, d in con.execute("select id, data from views")}
    con.close()
    return events, shadows, views


def odds_model(series):
    from trial import odds

    path = LAB / "odds.pkl"
    if path.exists():
        o = odds.Odds.__new__(odds.Odds)
        o.__dict__.update(pickle.loads(path.read_bytes()))
        o.series = series
        return o
    o = odds.Odds(series)
    path.write_bytes(pickle.dumps({k: v for k, v in o.__dict__.items() if k != "series"}))
    return o


async def run(a) -> int:
    from measure import realised
    from trial import desk, kb, lab, shadow

    series = realised.series()
    m = shadow.model()
    sources = set(a.sources.split(",")) if a.sources else set()
    o = odds_model(series) if "odds" in sources else None
    base = kb.load(ROOT / "out" / "replay" / "feeds") if "kb" in sources else None
    folder = LAB / "desk" / a.tag / a.replay
    folder.mkdir(parents=True, exist_ok=True)
    track_path = LAB / "tracks" / a.tag / f"{a.replay}.json"
    track_path.parent.mkdir(parents=True, exist_ok=True)
    track = {}
    if track_path.exists():
        track = {tuple(k.split("|")): v for k, v in json.loads(track_path.read_text()).items()}
    # the record: the replays before this one, then this one's mornings as they are answered
    agents_rows, desk_before = [], {}
    universe = []
    for name in a.after + [a.replay]:
        u = lab.moves(ROOT / "out" / "replay" / name / "state.db")
        universe += u
        agents_rows += u
        if name != a.replay:
            p = LAB / "tracks" / a.tag / f"{name}.json"
            if p.exists():
                desk_before.update({tuple(k.split("|")): v for k, v in json.loads(p.read_text()).items()})
    events, shadows, views = read(ROOT / "out" / "replay" / a.replay / "state.db")
    days = sorted(d for d, evs in events.items() if any(e.get("view_id") for e in evs))
    if a.days:
        days = days[: a.days]
    for day in days:
        out = folder / f"{day}.json"
        if out.exists():
            continue
        origin = shadow.realised.add_days(day, -1)
        evs = desk.drafts(day, events[day], shadows, views, m)
        history = None
        if "record" in sources:
            past = {**desk_before, **{k: v for k, v in track.items() if k[0] < day}}
            mine = lab.judge(past, [r for r in universe if (r["day"], r["horizon"], r["factor"]) in past], series)
            history = {"desk": mine, "analysts": [r for r in agents_rows if r["day"] < day]}
        p = desk.packet(day, origin, evs, series, m, o, base, history)
        t0 = time.time()
        try:
            got, meta = await desk.call(p)
        except Exception as exc:  # noqa: BLE001 — a morning that fails is written down and skipped
            print(day, "error", repr(exc)[:200], flush=True)
            continue
        calls = desk.parse(got, origin, day, series, m)
        track.update(calls)
        out.write_text(json.dumps({"packet": p, "reply": got, "meta": meta, "s": round(time.time() - t0, 1)},
                                  ensure_ascii=False, indent=1))
        track_path.write_text(desk.dumps(track))
        n = sum(1 for k, v in calls.items() if abs(v) >= 0.25 * desk.sigma(k[2], k[1], m))
        print(day, f"{len(evs)} events, {n} calls, {round(time.time() - t0)} s", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--replay", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--sources", default="odds,kb,record")
    ap.add_argument("--after", nargs="*", default=[])
    ap.add_argument("--days", type=int)
    a = ap.parse_args()
    state = LAB / "desk" / a.tag / f"{a.replay}.db"  # the calls' tokens and costs go here, never in the replay's
    state.parent.mkdir(parents=True, exist_ok=True)
    if not state.exists():
        shutil.copy(LAB / "market.db", state)
    env(state)
    from operonx.core.registry.resource_hub import ResourceHub

    ResourceHub.set_instance(ResourceHub.from_yaml(str(ROOT / "resources.yaml")))
    return asyncio.run(run(a))


if __name__ == "__main__":
    sys.exit(main())

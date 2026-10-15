"""Run a job's fetch: every series of the job, each from its sources in order (the first that answers with points
is used), kept in ``market_series`` and recorded in ``source_runs``.

The series and their sources are the ``price_sources`` configuration in force (owner Admin; version 1 is
data/market_sources.json). A tick asks from the series' last stored day (at most ``TICK_DAYS`` back); a backfill
asks from ``since``, sampling the sources that answer one day per request (VCB, PNJ, HNX) every ``DATED_STEP``
days so it stays polite.
"""

from __future__ import annotations

import time
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from market import sources, store
from market.sources import Fetched, Http, Request, _within

TICK_DAYS = 10  # a tick looks back this far when a series is new or a run was missed
DATED_STEP = 7  # a backfill asks the one-day-per-request sources once a week
PAUSE = 0.15  # seconds between two requests to the same host in a backfill


def catalogue() -> Dict[str, Any]:
    from control import config

    return config.data("price_sources")


def ticker_map() -> Dict[str, str]:
    from control import config

    return config.data("ticker_map")


def series_of(job: str) -> List[Dict[str, Any]]:
    return [s for s in catalogue()["series"] if s["job"] == job]


def _memo(get: Http, pause: float = 0.0) -> Http:
    """One answer per request within a run (HNX's one curve serves four tenors), and a pause between requests."""
    seen: Dict[tuple, bytes] = {}

    def call(req: Request) -> bytes:
        key = (req.method, req.url, req.body)
        if key not in seen:
            if pause and seen:
                time.sleep(pause)
            seen[key] = get(req)
        return seen[key]

    return call


def _window(series_id: str, today: date, since: Optional[date]) -> date:
    if since is not None:
        return since
    last = store.last_date(series_id)
    floor = today - timedelta(days=TICK_DAYS)
    return max(date.fromisoformat(last), floor) if last else floor


def fetch_series(
    spec: Dict[str, Any], start: date, end: date, get: Http, step: int = 1, pre: Optional[Dict[tuple, Any]] = None
) -> Dict[str, Any]:
    """One series from its sources in order; what was tried, and the points of the first that gave some. ``pre``
    holds answers already fetched together ({(source, symbol): Fetched or an exception})."""
    tried: List[Dict[str, Any]] = []
    tmap = ticker_map() if spec.get("ticker") else {}
    for s in spec["sources"]:
        s = {**s, "symbol": tmap.get(s["symbol"], s["symbol"])}  # a demo ticker → its exchange symbol
        name = s["source"]
        adapter = sources.ADAPTERS[name]
        kwargs: Dict[str, Any] = {"scale": float(s.get("scale", 1.0))}
        if name in sources.DATED:
            kwargs["step"] = step
        try:
            ready = (pre or {}).get((name, s["symbol"]))
            if isinstance(ready, Exception):
                raise ready
            if ready is not None:
                scale = kwargs["scale"]
                got: Fetched = Fetched([(d, v * scale) for d, v in _within(ready.points, start, end)], ready.url)
            else:
                got = adapter(s["symbol"], start, end, get, **kwargs)
        except Exception as exc:  # noqa: BLE001 — a source that fails hands over to the next
            tried.append({"source": name, "error": f"{type(exc).__name__}: {exc}"[:200]})
            continue
        tried.append({"source": name, "points": len(got.points)})
        if got.points:
            return {"source": name, "url": got.url, "points": got.points, "tried": tried}
    return {"source": None, "url": "", "points": [], "tried": tried}


def _msn_together(specs, starts, today: date, get: Http) -> Dict[tuple, Any]:
    """The series whose first source is MSN, in one request (the world job: ~1 request an hour, not 12)."""
    first = [s for s in specs if s["sources"][0]["source"] == "msn"]
    if len(first) < 2:
        return {}
    ids = [s["sources"][0]["symbol"] for s in first]
    try:
        got, url = sources.msn_many(ids, min(starts[s["id"]] for s in first), today, get)
    except Exception as exc:  # noqa: BLE001 — each series then records the failure and tries its fallback
        return {("msn", i): exc for i in ids}
    return {("msn", i): Fetched(got.get(i, []), url) for i in ids}


def run_job(
    job: str,
    get: Optional[Http] = None,
    today: Optional[date] = None,
    since: Optional[date] = None,
    only: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Fetch every series of ``job`` and keep what came back. ``get`` replaces the network (tests); ``since``
    makes it a backfill; ``only`` limits it to some series."""
    today = today or date.today()
    backfill = since is not None
    get = _memo(get or sources.http, PAUSE if backfill else 0.0)
    specs = [s for s in series_of(job) if not only or s["id"] in only]
    starts = {s["id"]: _window(s["id"], today, since) for s in specs}
    pre = _msn_together(specs, starts, today, get)
    out = []
    for spec in specs:
        start = starts[spec["id"]]
        t0 = time.time()
        got = fetch_series(spec, start, today, get, step=DATED_STEP if backfill else 1, pre=pre)
        n = store.put(spec["id"], got["source"], got["url"], got["points"]) if got["points"] else 0
        stale = not got["points"] and start >= today - timedelta(days=3)  # nothing new over a weekend is not a failure
        error = None
        if not got["points"] and not stale:
            error = "; ".join(f"{t['source']}: {t.get('error') or 'không có điểm mới'}" for t in got["tried"])
        store.record_run(job, spec["id"], got["source"], got["tried"], t0, time.time(), n, error)
        out.append({"series": spec["id"], "source": got["source"], "points": n, "error": error})
    return {
        "job": job,
        "series": out,
        "points": sum(x["points"] for x in out),
        "errors": sum(1 for x in out if x["error"]),
    }


def jobs() -> Dict[str, Dict[str, Any]]:
    return catalogue()["jobs"]

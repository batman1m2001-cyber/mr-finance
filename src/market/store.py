"""Market data kept in the state file (BRD_COMPLETION_PLAN F1, F-D11): the app reads these tables at request time,
never the outside sources.

- ``market_series``: one point per series and day (series, date, value, source, url, fetched_at). An hourly run
  updates the day's point.
- ``source_runs``: every fetch of every series by every job (job, series, source used, sources tried, start, end,
  points, error), for the source registry and its alerts.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Tuple

from wealth.paths import state_path

SCHEMA = """
create table if not exists market_series (
  series text not null, date text not null, value real not null, source text not null, url text not null,
  fetched_at real not null, primary key (series, date));
create table if not exists source_runs (
  id integer primary key autoincrement, job text not null, series text not null, source text,
  tried text not null, started real not null, finished real not null, points integer not null, error text);
create index if not exists source_runs_job on source_runs (job, started);
"""


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(SCHEMA)
        yield con
        con.commit()
    finally:
        con.close()


def put(series: str, source: str, url: str, points: List[Tuple[str, float]], at: Optional[float] = None) -> int:
    """Keep the points (a day's point is replaced by a newer fetch)."""
    at = time.time() if at is None else at
    with _db() as con:
        con.executemany(
            "insert into market_series values (?, ?, ?, ?, ?, ?) on conflict (series, date) do update set "
            "value = excluded.value, source = excluded.source, url = excluded.url, fetched_at = excluded.fetched_at",
            [(series, d, float(v), source, url, at) for d, v in points],
        )
    return len(points)


def record_run(
    job: str,
    series: str,
    source: Optional[str],
    tried: List[Dict[str, Any]],
    started: float,
    finished: float,
    points: int,
    error: Optional[str],
) -> None:
    with _db() as con:
        con.execute(
            "insert into source_runs (job, series, source, tried, started, finished, points, error) "
            "values (?, ?, ?, ?, ?, ?, ?, ?)",
            (job, series, source, json.dumps(tried, ensure_ascii=False), started, finished, points, error),
        )


def points(series: str, start: Optional[str] = None, end: Optional[str] = None) -> List[Tuple[str, float]]:
    q, args = "select date, value from market_series where series = ?", [series]
    if start:
        q += " and date >= ?"
        args.append(start)
    if end:
        q += " and date <= ?"
        args.append(end)
    with _db() as con:
        return [(r["date"], r["value"]) for r in con.execute(q + " order by date", args)]


def last_date(series: str) -> Optional[str]:
    with _db() as con:
        row = con.execute("select max(date) as d from market_series where series = ?", (series,)).fetchone()
    return row["d"] if row else None


def coverage() -> Dict[str, Dict[str, Any]]:
    """Per series: first and last day, number of points, the last value, its source and when it was fetched."""
    with _db() as con:
        rows = con.execute(
            "select s.series, min(s.date) as first, max(s.date) as last, count(*) as n, "
            "(select value from market_series x where x.series = s.series order by date desc limit 1) as value, "
            "(select source from market_series x where x.series = s.series order by date desc limit 1) as source, "
            "max(s.fetched_at) as fetched_at from market_series s group by s.series"
        ).fetchall()
    return {r["series"]: dict(r) for r in rows}


def runs(job: Optional[str] = None, limit: int = 200) -> List[Dict[str, Any]]:
    q, args = "select * from source_runs", []
    if job:
        q += " where job = ?"
        args.append(job)
    with _db() as con:
        rows = con.execute(q + " order by id desc limit ?", [*args, int(limit)]).fetchall()
    return [{**dict(r), "tried": json.loads(r["tried"])} for r in rows]


def job_health() -> Dict[str, Dict[str, Any]]:
    """Per job: its last run, last success and last error (a run is the series fetched in one tick)."""
    with _db() as con:
        rows = con.execute(
            "select job, max(finished) as last_run, "
            "max(case when error is null then finished end) as last_ok, "
            "max(case when error is not null then finished end) as last_error_at "
            "from source_runs group by job"
        ).fetchall()
        out = {r["job"]: dict(r) for r in rows}
        for job, h in out.items():
            err = con.execute(
                "select series, error from source_runs where job = ? and error is not null order by id desc limit 1",
                (job,),
            ).fetchone()
            h["last_error"] = f"{err['series']}: {err['error']}" if err else None
    return out


def reset() -> None:
    """Demo reset keeps the market data: it is fetched, not made by the demo."""

"""One SQLite helper for the news-impact tables (events, views, challenges, decisions, agent runs,
and in N3 the application runs and the audit chain), in the demo's state file.

Each table keeps a few columns to filter and index on and the whole record in a JSON ``data``
column (BRD §11.4, and how the rest of this app stores things). A write is one transaction: every
table a step touches is written together, or none is. Readable ids come from ``counters``.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from control.audit import SCHEMA as AUDIT_SCHEMA
from wealth.paths import state_path

SCHEMA = """
create table if not exists counters (name text primary key, value integer not null);
create table if not exists events (
  id text primary key, created real not null, status text not null, data text not null);
create table if not exists views (
  id text primary key, event_id text not null, version integer not null, status text not null,
  created real not null, data text not null, unique (event_id, version));
create index if not exists views_event on views (event_id);
create table if not exists challenges (
  id text primary key, view_id text not null, stage text not null, created real not null, data text not null);
create index if not exists challenges_view on challenges (view_id);
create table if not exists decisions (
  id text primary key, view_id text not null, action text not null, idem_key text unique,
  created real not null, data text not null);
create index if not exists decisions_view on decisions (view_id);
create table if not exists agent_runs (
  id text primary key, agent text not null, subject_id text not null, created real not null, data text not null);
create index if not exists agent_runs_subject on agent_runs (subject_id);
create table if not exists application_runs (
  id text primary key, view_id text not null, event_id text not null, status text not null,
  idem_key text unique, created real not null, data text not null);
create index if not exists application_runs_view on application_runs (view_id);
create table if not exists run_snapshots (id text primary key, created real not null, data text not null);
create table if not exists family_impacts (
  id text primary key, run_id text not null, family_id text not null, data text not null,
  unique (run_id, family_id));
create index if not exists family_impacts_family on family_impacts (family_id);
create table if not exists research_items (
  id text primary key, kind text not null, status text not null, created real not null, data text not null);
create table if not exists config_versions (
  id text primary key, kind text not null, version integer not null, status text not null,
  created real not null, data text not null, unique (kind, version));
create table if not exists goal_outflows (
  goal_id text primary key, family_id text not null, created real not null, data text not null);
create table if not exists forecasts (
  id text primary key, view_id text not null, factor text not null, horizon text not null, origin text not null,
  due text not null, created real not null, scored real, data text not null);
create index if not exists forecasts_open on forecasts (scored, due);
create table if not exists agent_jobs (
  id text primary key, event_id text not null, status text not null, created real not null, data text not null);
create index if not exists agent_jobs_open on agent_jobs (status, created);
create table if not exists external_outputs (
  id text primary key, status text not null, received real not null, signed integer not null,
  package_hash text not null, body text not null, data text not null);
create index if not exists external_outputs_open on external_outputs (status, received);
create table if not exists zone_syncs (
  id text primary key, at real not null, status text not null, bundle_hash text not null, data text not null);
create table if not exists zone_outbox (
  id text primary key, event_id text not null, status text not null, created real not null, data text not null);
create index if not exists zone_outbox_open on zone_outbox (status, created);
create table if not exists alerts (
  id text primary key, kind text not null, key text not null, status text not null, created real not null,
  data text not null);
create index if not exists alerts_open on alerts (kind, key, status);
"""

TABLES = (
    "events",
    "views",
    "challenges",
    "decisions",
    "agent_runs",
    "application_runs",
    "run_snapshots",
    "family_impacts",
    "config_versions",
    "forecasts",
    "agent_jobs",
    "external_outputs",
    "zone_syncs",
    "zone_outbox",
    "alerts",
    "counters",
)


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(SCHEMA + AUDIT_SCHEMA)
        con.execute("begin immediate")
        yield con
        con.execute("commit")
    except BaseException:
        if con.in_transaction:
            con.execute("rollback")
        raise
    finally:
        con.close()


def next_seq(con: sqlite3.Connection, name: str) -> int:
    row = con.execute("select value from counters where name = ?", (name,)).fetchone()
    value = (row["value"] if row else 0) + 1
    con.execute("insert or replace into counters values (?, ?)", (name, value))
    return value


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def load(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    d = json.loads(row["data"])
    for k in row.keys():  # the columns are authoritative (status changes are written there)
        if k != "data":
            d[k] = row[k]
    return d


def reset() -> None:
    """The demo starts over: every news-impact record goes (the fetched news stays, news.store). The
    audit log refuses DELETE by design, so the demo reset drops it and a new chain starts."""
    with tx() as con:
        for t in TABLES:
            con.execute(f"delete from {t}")
        con.execute("drop table if exists audit_log")
    from control import config

    config.clear_cache()

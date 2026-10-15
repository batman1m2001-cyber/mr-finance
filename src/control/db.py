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
"""

TABLES = ("events", "views", "challenges", "decisions", "agent_runs", "counters")


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(SCHEMA)
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
    """The demo starts over: every news-impact record goes (the fetched news stays, news.store)."""
    with tx() as con:
        for t in TABLES:
            con.execute(f"delete from {t}")

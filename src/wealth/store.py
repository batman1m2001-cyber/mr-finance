"""What clients add, kept in one SQLite file: holdings read from a statement or declared in the
chat, their dependents and income, risk results, alerts and the RM queue.

Each call opens its own connection: ops run on several threads, and SQLite is happiest that way.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional

from wealth.paths import state_path

SCHEMA = """
create table if not exists holdings (
  key text primary key, client_id text not null, source text not null, data text not null,
  created real not null);
create table if not exists profile (
  id text primary key, client_id text not null, kind text not null, data text not null,
  created real not null);
create table if not exists results (
  client_id text not null, kind text not null, data text not null, created real not null,
  primary key (client_id, kind));
create table if not exists reviews (
  id text primary key, client_id text not null, kind text not null, title text not null,
  data text not null, status text not null, note text, created real not null, decided real);
"""


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10)
    try:
        con.executescript(SCHEMA)
        yield con
        con.commit()
    finally:
        con.close()


# ── holdings a client added ─────────────────────────────────────────────


def put_holdings(client_id: str, source: str, holdings: List[Dict[str, Any]]) -> int:
    """Add or replace holdings by their ``key`` (a statement read twice replaces itself)."""
    with _db() as con:
        for h in holdings:
            con.execute(
                "insert or replace into holdings values (?, ?, ?, ?, ?)",
                (h["key"], client_id, source, json.dumps(h, ensure_ascii=False), time.time()),
            )
    return len(holdings)


def holdings(client_id: str, source: Optional[str] = None) -> List[Dict[str, Any]]:
    q = "select data from holdings where client_id = ?"
    args: List[Any] = [client_id]
    if source:
        q += " and source = ?"
        args.append(source)
    with _db() as con:
        return [json.loads(r[0]) for r in con.execute(q + " order by created", args)]


# ── profile items: dependents, income, events ────────────────────────────


def add_profile(client_id: str, kind: str, data: Dict[str, Any]) -> str:
    item_id = data.get("id") or f"{kind}-{uuid.uuid4().hex[:8]}"
    with _db() as con:
        con.execute(
            "insert or replace into profile values (?, ?, ?, ?, ?)",
            (
                item_id,
                client_id,
                kind,
                json.dumps({**data, "id": item_id}, ensure_ascii=False),
                time.time(),
            ),
        )
    return item_id


def profile(client_id: str, kind: Optional[str] = None) -> List[Dict[str, Any]]:
    q = "select data from profile where client_id = ?"
    args: List[Any] = [client_id]
    if kind:
        q += " and kind = ?"
        args.append(kind)
    with _db() as con:
        return [json.loads(r[0]) for r in con.execute(q + " order by created", args)]


# ── the latest result of a kind: a risk test, the alerts ────────────────


def put_result(client_id: str, kind: str, data: Any) -> None:
    with _db() as con:
        con.execute(
            "insert or replace into results values (?, ?, ?, ?)",
            (client_id, kind, json.dumps(data, ensure_ascii=False), time.time()),
        )


def result(client_id: str, kind: str) -> Optional[Any]:
    with _db() as con:
        row = con.execute(
            "select data from results where client_id = ? and kind = ?", (client_id, kind)
        ).fetchone()
    return json.loads(row[0]) if row else None


# ── the RM queue ─────────────────────────────────────────────────────────


def propose(client_id: str, kind: str, title: str, data: Dict[str, Any]) -> str:
    item_id = f"R-{uuid.uuid4().hex[:8]}"
    with _db() as con:
        con.execute(
            "insert into reviews values (?, ?, ?, ?, ?, 'pending', null, ?, null)",
            (item_id, client_id, kind, title, json.dumps(data, ensure_ascii=False), time.time()),
        )
    return item_id


def decide(item_id: str, status: str, note: str = "") -> Optional[Dict[str, Any]]:
    if status not in ("approved", "rejected"):
        raise ValueError(f"a decision is approved or rejected, not {status!r}")
    with _db() as con:
        cur = con.execute(
            "update reviews set status = ?, note = ?, decided = ?"
            " where id = ? and status = 'pending'",
            (status, note, time.time(), item_id),
        )
        if not cur.rowcount:
            return None
    return review(item_id)


def review(item_id: str) -> Optional[Dict[str, Any]]:
    with _db() as con:
        row = con.execute("select * from reviews where id = ?", (item_id,)).fetchone()
    return _review_row(row) if row else None


def reviews(client_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    q, args = "select * from reviews where 1=1", []
    if client_id:
        q += " and client_id = ?"
        args.append(client_id)
    if status:
        q += " and status = ?"
        args.append(status)
    with _db() as con:
        return [_review_row(r) for r in con.execute(q + " order by created desc", args)]


def _review_row(r: Any) -> Dict[str, Any]:
    return {
        "id": r[0],
        "client_id": r[1],
        "kind": r[2],
        "title": r[3],
        "data": json.loads(r[4]),
        "status": r[5],
        "note": r[6],
        "created": r[7],
        "decided": r[8],
    }


def reset() -> None:
    """Forget everything clients added: the demo starts over."""
    with _db() as con:
        for table in ("holdings", "profile", "results", "reviews"):
            con.execute(f"delete from {table}")

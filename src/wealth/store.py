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

from control import crypto
from wealth.paths import ensure_schema, state_path


def _seal(table: str, row_id: Any, column: str, text: Optional[str]) -> Optional[str]:
    """Sealed when column keys are set (BRD-NFR-07, control/crypto.py); the row's place is the associated data."""
    return crypto.seal(text, crypto.where(table, row_id, column))


def _open(table: str, row_id: Any, column: str, text: Optional[str]) -> Optional[str]:
    return crypto.open_(text, crypto.where(table, row_id, column))


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
        ensure_schema(con, path, "wealth", SCHEMA)
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
                (
                    h["key"],
                    client_id,
                    source,
                    _seal("holdings", h["key"], "data", json.dumps(h, ensure_ascii=False)),
                    time.time(),
                ),
            )
    return len(holdings)


def holdings(client_id: str, source: Optional[str] = None) -> List[Dict[str, Any]]:
    q = "select key, data from holdings where client_id = ?"
    args: List[Any] = [client_id]
    if source:
        q += " and source = ?"
        args.append(source)
    with _db() as con:
        return [json.loads(_open("holdings", r[0], "data", r[1])) for r in con.execute(q + " order by created", args)]


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
                _seal("profile", item_id, "data", json.dumps({**data, "id": item_id}, ensure_ascii=False)),
                time.time(),
            ),
        )
    return item_id


def profile(client_id: str, kind: Optional[str] = None) -> List[Dict[str, Any]]:
    q = "select id, data from profile where client_id = ?"
    args: List[Any] = [client_id]
    if kind:
        q += " and kind = ?"
        args.append(kind)
    with _db() as con:
        return [json.loads(_open("profile", r[0], "data", r[1])) for r in con.execute(q + " order by created", args)]


def _said(d: Dict[str, Any]) -> Dict[str, Any]:
    # what was declared, not how or when: no id, no path (chat, form), no free-text place; an empty field is no detail
    return {k: v for k, v in d.items() if k not in ("id", "via", "location") and v not in (None, 0, "")}


def same_profile(client_id: str, kind: str, data: Dict[str, Any]) -> Optional[str]:
    """The id of the client's item of this kind with the same details as ``data``, or None: said again in a later turn,
    the same land is the same land (on 2026-10-10 the demo sentence sent twice counted Đất Long Thành twice, 9 tỷ)."""
    want = _said(data)
    return next((d["id"] for d in profile(client_id, kind) if _said(d) == want), None)


def created(item_id: str) -> float:
    """When a profile item was added (0 when unknown)."""
    with _db() as con:
        row = con.execute("select created from profile where id = ?", (item_id,)).fetchone()
    return row[0] if row else 0.0


# ── the latest result of a kind: a risk test, the alerts ────────────────


def put_result(client_id: str, kind: str, data: Any) -> None:
    with _db() as con:
        con.execute(
            "insert or replace into results values (?, ?, ?, ?)",
            (
                client_id,
                kind,
                _seal("results", (client_id, kind), "data", json.dumps(data, ensure_ascii=False)),
                time.time(),
            ),
        )


def result(client_id: str, kind: str) -> Optional[Any]:
    with _db() as con:
        row = con.execute("select data from results where client_id = ? and kind = ?", (client_id, kind)).fetchone()
    return json.loads(_open("results", (client_id, kind), "data", row[0])) if row else None


# ── the RM queue ─────────────────────────────────────────────────────────


def propose(client_id: str, kind: str, title: str, data: Dict[str, Any], status: str = "pending") -> str:
    """Into the queue: ``pending`` waits for the RM; ``pending_cio`` (an allocation's actions, Q-29) for the CIO."""
    item_id = f"R-{uuid.uuid4().hex[:8]}"
    with _db() as con:
        con.execute(
            "insert into reviews values (?, ?, ?, ?, ?, ?, null, ?, null)",
            (
                item_id,
                client_id,
                kind,
                _seal("reviews", item_id, "title", title),
                _seal("reviews", item_id, "data", json.dumps(data, ensure_ascii=False)),
                status,
                time.time(),
            ),
        )
    return item_id


def decide(item_id: str, status: str, note: str = "", by: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The RM's decision, once. With ``by`` (the RM deciding), the item keeps who decided and the decision goes into
    the audit chain (``review.decide``, BRD-KPI-05); without it, as the queue did before (a test of the old records)."""
    if status not in ("approved", "rejected"):
        raise ValueError(f"a decision is approved or rejected, not {status!r}")
    if by is None:
        with _db() as con:
            cur = con.execute(
                "update reviews set status = ?, note = ?, decided = ? where id = ? and status = 'pending'",
                (status, _seal("reviews", item_id, "note", note), time.time(), item_id),
            )
            if not cur.rowcount:
                return None
        return review(item_id)
    # an item queued for an expert before OWN-FB-18 waits for its RM now: the RM's approval is the last
    was = "pending_specialist" if (review(item_id) or {}).get("status") == "pending_specialist" else "pending"
    return move(item_id, was, status, by, "review.decide", {"decided_by": by}, note=note)


def move(
    item_id: str,
    was: str,
    status: str,
    by: str,
    action: str,
    data: Dict[str, Any],
    note: Optional[str] = None,
    audit_data: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """An item from ``was`` to ``status``, ``data`` merged into its record, ``note`` (when given) as its note, and
    the step in the audit chain as ``action``; None when the item is not ``was`` (any more)."""
    from control import audit, db

    item = review(item_id)
    if item is None or item["status"] != was:
        return None
    body = json.dumps({**item["data"], **data}, ensure_ascii=False)
    sets, args = "status = ?, data = ?", [status, _seal("reviews", item_id, "data", body)]
    if note is not None:
        sets += ", note = ?"
        args.append(_seal("reviews", item_id, "note", note))
    if status in ("approved", "rejected"):
        sets += ", decided = ?"
        args.append(time.time())
    with db.tx() as con:
        cur = con.execute(f"update reviews set {sets} where id = ? and status = ?", (*args, item_id, was))
        if not cur.rowcount:
            return None
        audit.append(
            con, by, action, item_id, {"client_id": item["client_id"], "from": was, "to": status, **(audit_data or {})}
        )
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
        "title": _open("reviews", r[0], "title", r[3]),
        "data": json.loads(_open("reviews", r[0], "data", r[4])),
        "status": r[5],
        "note": _open("reviews", r[0], "note", r[6]),
        "created": r[7],
        "decided": r[8],
    }


def reset() -> None:
    """Forget everything clients added: the demo starts over."""
    with _db() as con:
        for table in ("holdings", "profile", "results", "reviews"):
            con.execute(f"delete from {table}")

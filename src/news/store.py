"""News items and ingest runs, in the demo's SQLite file (data/state.db, or ``MF_STATE``).

An item is kept once: by its link (http/https, trailing slash and tracking query ignored) and by
its source + title. Refused items are kept too, with the reason, so Compliance can see what the
gates stopped; they never reach the inbox. Ids read ``NW-000123``.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Tuple

from control import audit
from control.audit import SCHEMA as AUDIT_SCHEMA
from wealth.paths import ensure_schema, state_path

STATUSES = ("new", "dismissed", "grouped", "refused")

SCHEMA = """
create table if not exists news_items (
  id text primary key, seq integer not null unique, source text not null, url_key text not null unique,
  title_key text not null, published real, ingested real not null, kind text, status text not null,
  relevance text, event_type text, held integer not null default 0, data text not null);
create index if not exists news_items_published on news_items (published);
create index if not exists news_items_title on news_items (title_key);
create table if not exists news_runs (
  id integer primary key autoincrement, at real not null, data text not null);
create table if not exists reference_stories (
  id text primary key, published real, first_seen real not null, judged real, collected integer, data text not null);
create index if not exists reference_stories_open on reference_stories (judged, first_seen);
"""


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        ensure_schema(con, path, "news", SCHEMA + AUDIT_SCHEMA)
        con.execute("begin immediate")
        yield con
        con.execute("commit")
    except BaseException:
        if con.in_transaction:
            con.execute("rollback")
        raise
    finally:
        con.close()


def add(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """Keep new items; return them as kept (with their ids) and how many were already there."""
    added, dup = [], 0
    with _db() as con:
        seq = con.execute("select coalesce(max(seq), 0) from news_items").fetchone()[0]
        for it in items:
            seen = con.execute(
                "select 1 from news_items where url_key = ? or title_key = ?", (it["url_key"], it["title_key"])
            ).fetchone()
            if seen:
                dup += 1
                continue
            seq += 1
            item_id = f"NW-{seq:06d}"
            row = {**it, "id": item_id}
            con.execute(
                "insert into news_items values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item_id,
                    seq,
                    it["source"],
                    it["url_key"],
                    it["title_key"],
                    it.get("published"),
                    it["ingested"],
                    it.get("kind"),
                    it["status"],
                    it.get("relevance"),
                    it.get("event_type"),
                    1 if it.get("restricted") else 0,
                    json.dumps(row, ensure_ascii=False),
                ),
            )
            added.append(row)
        if added:
            audit.append(
                con,
                "system:ingest",
                "news.add",
                "news",
                {"ids": [r["id"] for r in added], "refused": [r["id"] for r in added if r["status"] == "refused"]},
            )
    return added, dup


def record_run(summary: Dict[str, Any]) -> int:
    with _db() as con:
        cur = con.execute("insert into news_runs (at, data) values (?, ?)", (summary["at"], json.dumps(summary)))
        return int(cur.lastrowid)


def last_run() -> Optional[Dict[str, Any]]:
    with _db() as con:
        row = con.execute("select data from news_runs order by id desc limit 1").fetchone()
    return json.loads(row["data"]) if row else None


def _item(row: sqlite3.Row) -> Dict[str, Any]:
    d = json.loads(row["data"])
    d["status"] = row["status"]
    d["held"] = bool(row["held"])
    return d


def inbox(
    source: Optional[str] = None,
    kind: Optional[str] = None,
    status: str = "new",
    relevance: Optional[str] = None,
    since: Optional[float] = None,
    query: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Newest first. ``status`` "all" shows every status but refused; "refused" shows only those."""
    where, args = [], []
    if status == "all":
        where.append("status != 'refused'")
    else:
        where.append("status = ?")
        args.append(status)
    for col, val in (("source", source), ("kind", kind), ("relevance", relevance)):
        if val:
            where.append(f"{col} = ?")
            args.append(val)
    if since:
        where.append("published >= ?")
        args.append(since)
    sql = f"select * from news_items where {' and '.join(where)} order by published desc, seq desc"
    with _db() as con:
        rows = con.execute(sql, args).fetchall()
    out = [_item(r) for r in rows]
    if query:
        q = query.lower()
        out = [it for it in out if q in it["title"].lower() or q in it.get("summary", "").lower()]
    return out[:limit]


def get(ids: List[str]) -> List[Dict[str, Any]]:
    if not ids:
        return []
    with _db() as con:
        rows = con.execute(f"select * from news_items where id in ({','.join('?' * len(ids))})", ids).fetchall()
    by = {r["id"]: _item(r) for r in rows}
    return [by[i] for i in ids if i in by]


def by_url_key(key: str) -> Optional[Dict[str, Any]]:
    """The item fetched from this address (``rules.url_key``), if TCB has it: how the inbox matches the AI zone's
    news to news TCB fetched itself."""
    with _db() as con:
        r = con.execute("select * from news_items where url_key = ?", (key,)).fetchone()
    return _item(r) if r else None


def counts(since: Optional[float] = None) -> Dict[str, Any]:
    """Counted in the database, never the length of a capped list (``inbox`` stops at its limit: the assistant said
    200 for 1,415, CIO chat 2026-10-24): items by status, and those fetched since ``since`` by source."""
    with _db() as con:
        by_status = dict(con.execute("select status, count(*) from news_items group by status").fetchall())
        fetched = dict(
            con.execute(
                "select source, count(*) from news_items where ingested >= ? and status != 'refused' group by source",
                (since or 0,),
            ).fetchall()
        )
    return {"by_status": by_status, "fetched": fetched}


def counts_by_hour(hours: int = 24, now: Optional[float] = None) -> Dict[str, List[int]]:
    """Items published per hour per source over the last ``hours`` (oldest first): feed health."""
    now = now or time.time()
    start = now - hours * 3600
    out: Dict[str, List[int]] = {}
    with _db() as con:
        rows = con.execute(
            "select source, published from news_items where status != 'refused' and published >= ?", (start,)
        ).fetchall()
    for r in rows:
        slot = min(hours - 1, int((r["published"] - start) // 3600))
        out.setdefault(r["source"], [0] * hours)[slot] += 1
    return out


def set_status(ids: List[str], status: str, by: str, note: str = "") -> int:
    if status not in STATUSES or status == "refused":
        raise ValueError(f"status {status!r} cannot be set by hand")
    changed = 0
    with _db() as con:
        for item_id in ids:
            row = con.execute("select data, status from news_items where id = ?", (item_id,)).fetchone()
            if row is None or row["status"] == "refused":
                continue
            d = json.loads(row["data"])
            d.setdefault("history", []).append({"at": time.time(), "by": by, "status": status, "note": note})
            con.execute(
                "update news_items set status = ?, data = ? where id = ?",
                (status, json.dumps(d, ensure_ascii=False), item_id),
            )
            changed += 1
        if changed:
            audit.append(con, by, f"news.{status}", ",".join(ids), {"note": note})
    return changed


def clear_hold(item_id: str, by: str, note: str) -> bool:
    """Compliance lets a held item through (BR-04)."""
    with _db() as con:
        row = con.execute("select data, held from news_items where id = ?", (item_id,)).fetchone()
        if row is None or not row["held"]:
            return False
        d = json.loads(row["data"])
        d["cleared"] = {"at": time.time(), "by": by, "note": note}
        con.execute(
            "update news_items set held = 0, data = ? where id = ?", (json.dumps(d, ensure_ascii=False), item_id)
        )
        audit.append(con, by, "news.release", item_id, {"note": note, "restricted": d.get("restricted", [])})
    return True


def reset() -> None:
    """The demo starts over: fetched news stays, every item back to new, holds back on."""
    with _db() as con:
        rows = con.execute("select id, data from news_items where status != 'refused'").fetchall()
        for r in rows:
            d = json.loads(r["data"])
            d.pop("history", None)
            d.pop("cleared", None)
            con.execute(
                "update news_items set status = 'new', held = ?, data = ? where id = ?",
                (1 if d.get("restricted") else 0, json.dumps(d, ensure_ascii=False), r["id"]),
            )

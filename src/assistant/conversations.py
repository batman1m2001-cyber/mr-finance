"""Conversations on the server (A3, assistant.md §5, ADR-0027): listed, resumed on another device, deleted.

``assistant.db`` beside the state file (WAL), apart from the business data:

- ``conversations``: id, owner, role, client, title, created, updated, turns.
- ``turns``: what the panel showed, in order — the question and the answer as sent — to draw it again anywhere.
- ``operonx_agents_items``: the model's side (operonx-agents' ``SQLiteSession``, one shared connection per file):
  what it was sent and what it said, one session per mode (``read``: a model allowed to read client data;
  ``template``: the scrubbed question and the tools' statuses). When a prompt passes the budget
  (``ContextPolicy``), older exchanges become a summary item; nothing is deleted.
- ``assistant_runs``: a run parked on a write (operonx-agents' run state).

With ``MF_DATA_KEYS`` set, the text is sealed (control/crypto.py): titles, turns, session items, run states; each
with its conversation (or run) as its place, so it does not open elsewhere. Every read and write is keyed by the
owner the server resolved (``owner``) and the role: no request names an owner.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from operonx_agents import RunState, SQLiteSession

from assistant.base import Ctx
from control import crypto
from wealth.paths import state_path

TITLE = 80  # characters of the first question kept as the title
SCHEMA = """
create table if not exists conversations (id text primary key, owner text not null, role text not null,
    client_id text, title text, created real not null, updated real not null, turns integer not null default 0);
create index if not exists conversations_owner on conversations (owner, role, updated);
create table if not exists turns (conversation_id text not null, seq integer not null, at real not null,
    question text, answer text not null, primary key (conversation_id, seq));
create table if not exists assistant_runs (run_id text primary key, state text not null, updated real not null);
create table if not exists parked (run_id text primary key, owner text not null, role text not null,
    conversation_id text not null, client_id text, scope text, reads integer not null, calls text not null,
    created real not null);
"""


def db_path() -> Path:
    return state_path().with_name("assistant.db")


_READY: set = set()


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(db_path(), timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    try:
        p = str(db_path())
        if p not in _READY:
            con.execute("pragma journal_mode=wal")
            cols = {r[1] for r in con.execute("pragma table_info(parked)")}
            if cols and "conversation_id" not in cols:  # A2's parked writes (ten minutes' worth): not resumable,
                con.execute("drop table parked")  # and their run states, stored unsealed
                con.execute("drop table if exists operonx_agents_runs")
            con.executescript(SCHEMA)
            _READY.add(p)
        yield con
    finally:
        con.close()


def owner(ctx: Ctx) -> str:
    return ctx.user or f"client:{ctx.client_id or '-'}"


def _place(table: str, row_id: Any, column: str) -> bytes:
    return crypto.where(table, row_id, column)


def _seal_json(obj: Any, place: bytes) -> str:
    text = json.dumps(obj, ensure_ascii=False, default=str)
    return crypto.seal(text, place) if crypto.on() else text


def _open_json(text: Optional[str], place: bytes) -> Any:
    return None if text is None else json.loads(crypto.open_(text, place))


# -- conversations -----------------------------------------------------------------------------------------------


def start(ctx: Ctx, question: str) -> str:
    cid = uuid.uuid4().hex[:16]
    now = time.time()
    title = " ".join(str(question or "").split())[:TITLE] or "Cuộc trò chuyện"
    with db() as con:
        con.execute(
            "insert into conversations values (?, ?, ?, ?, ?, ?, ?, 0)",
            (cid, owner(ctx), ctx.role, ctx.client_id, crypto.seal(title, _place("conversations", cid, "title")),
             now, now),
        )  # fmt: skip
    return cid


def own(ctx: Ctx, cid: Optional[str]) -> Dict[str, Any]:
    """The conversation, when it is this person's in this role; else ValueError."""
    with db() as con:
        row = con.execute("select * from conversations where id = ?", (str(cid or ""),)).fetchone()
    if row is None or row["owner"] != owner(ctx) or row["role"] != ctx.role:
        raise ValueError("Không có cuộc trò chuyện này")
    return _row(row)


def _row(row: sqlite3.Row) -> Dict[str, Any]:
    out = dict(row)
    out["title"] = crypto.open_(out["title"], _place("conversations", out["id"], "title"))
    out.pop("owner", None)
    return out


def listing(ctx: Ctx, limit: int = 50) -> List[Dict[str, Any]]:
    with db() as con:
        rows = con.execute(
            "select * from conversations where owner = ? and role = ? order by updated desc limit ?",
            (owner(ctx), ctx.role, int(limit)),
        ).fetchall()
    return [_row(r) for r in rows]


def record(cid: str, question: Optional[str], answer: Dict[str, Any]) -> int:
    """A turn as the panel showed it; the conversation's ``updated`` and count move with it."""
    now = time.time()
    with db() as con:
        con.execute("begin immediate")
        (seq,) = con.execute(
            "select coalesce(max(seq), -1) + 1 from turns where conversation_id = ?", (cid,)
        ).fetchone()
        place = _place("turns", (cid, seq), "turn")
        con.execute(
            "insert into turns values (?, ?, ?, ?, ?)",
            (cid, seq, now, crypto.seal(question, place) if question else None, _seal_json(answer, place)),
        )
        con.execute("update conversations set updated = ?, turns = turns + 1 where id = ?", (now, cid))
        con.execute("commit")
    return seq


def turns_of(cid: str) -> List[Dict[str, Any]]:
    with db() as con:
        rows = con.execute("select * from turns where conversation_id = ? order by seq", (cid,)).fetchall()
    out = []
    for r in rows:
        place = _place("turns", (cid, r["seq"]), "turn")
        out.append(
            {
                "seq": r["seq"],
                "at": r["at"],
                "question": crypto.open_(r["question"], place),
                "answer": _open_json(r["answer"], place),
            }
        )
    return out


def delete(ctx: Ctx, cid: str) -> int:
    """The conversation, its turns and the model's side of it; parked runs of it no longer run; then scrubbed from
    the disk. Returns the turns deleted."""
    c = own(ctx, cid)
    with db() as con:
        con.execute("begin immediate")
        erase(con, cid)
        con.execute("commit")
    scrub()
    return c["turns"]


def erase(con: sqlite3.Connection, cid: str) -> int:
    """Every row of conversation ``cid`` (inside the caller's transaction). Returns its turns."""
    (n,) = con.execute("select count(*) from turns where conversation_id = ?", (cid,)).fetchone()
    con.execute("delete from turns where conversation_id = ?", (cid,))
    if _has(con, "operonx_agents_items"):
        con.execute("delete from operonx_agents_items where session_id like ?", (session_id(cid, "%"),))
    for (rid,) in con.execute("select run_id from parked where conversation_id = ?", (cid,)).fetchall():
        con.execute("delete from assistant_runs where run_id = ?", (rid,))
    con.execute("delete from parked where conversation_id = ?", (cid,))
    con.execute("delete from conversations where id = ?", (cid,))
    return n


def scrub() -> None:
    """What was deleted, gone from the disk too: the log checkpointed and emptied, the file rebuilt without the
    freed pages (SQLite otherwise leaves deleted rows readable in both until they are reused)."""
    with db() as con:
        con.execute("pragma wal_checkpoint(TRUNCATE)")
        con.execute("vacuum")
        con.execute("pragma wal_checkpoint(TRUNCATE)")


def _has(con: sqlite3.Connection, table: str) -> bool:
    return con.execute("select 1 from sqlite_master where type = 'table' and name = ?", (table,)).fetchone() is not None


# -- the model's side: the session and the run store, sealed -----------------------------------------------------


def session_id(cid: str, mode: str) -> str:
    return f"conv:{cid}:{mode}"


class Session(crypto.SealedSession):
    """operonx-agents' ``SQLiteSession`` for one conversation in one mode, each item sealed (control/crypto.py)."""

    def __init__(self, cid: str, mode: str) -> None:
        sid = session_id(cid, mode)
        super().__init__(SQLiteSession(sid, db_path()), sid)

    def close(self) -> None:
        self.inner.close()


class Runs:
    """The run store (a run parked on a write), each state sealed with its run as its place."""

    async def save(self, state: RunState) -> None:
        text = state.dumps()
        with db() as con:
            con.execute(
                "insert or replace into assistant_runs values (?, ?, ?)",
                (state.run_id, crypto.seal(text, _place("assistant_runs", state.run_id, "state")), time.time()),
            )

    async def load(self, run_id: str) -> Optional[RunState]:
        with db() as con:
            row = con.execute("select state from assistant_runs where run_id = ?", (run_id,)).fetchone()
        return None if row is None else RunState.loads(crypto.open_(row[0], _place("assistant_runs", run_id, "state")))

    async def delete(self, run_id: str) -> None:
        with db() as con:
            con.execute("delete from assistant_runs where run_id = ?", (run_id,))


RUNS = Runs()


# -- key rotation (scripts/rotate_keys.py) ----------------------------------------------------------------------


def census(con: sqlite3.Connection) -> Dict[str, int]:
    """How many of assistant.db's values each key seals, and how many are plain (as ``crypto.census``)."""
    out: Dict[str, int] = {}

    def count(v: Optional[str]) -> None:
        if v is not None:
            k = v[len(crypto.PREFIX) :].partition(":")[0] if crypto.sealed(v) else "plain"
            out[k] = out.get(k, 0) + 1

    for sql in (
        "select title from conversations",
        "select question from turns",
        "select answer from turns",
        "select state from assistant_runs",
    ):
        for (v,) in con.execute(sql):
            count(v)
    if _has(con, "operonx_agents_items"):
        for (item,) in con.execute("select item from operonx_agents_items"):
            raw = json.loads(item)
            count(raw["sealed"] if isinstance(raw, dict) and set(raw) == {"sealed"} else "plain")
    return out


def rotate(con: sqlite3.Connection) -> Dict[str, int]:
    """Every sealed value of assistant.db opened and sealed again under the current key; plain ones sealed."""
    out = {"conversations": 0, "turns": 0, "assistant_runs": 0, "operonx_agents_items": 0}
    if not crypto.on():
        return out

    def again(text: Optional[str], place: bytes) -> Optional[str]:
        return None if text is None else crypto.seal(crypto.open_(text, place), place)

    for cid, title in con.execute("select id, title from conversations").fetchall():
        place = _place("conversations", cid, "title")
        con.execute("update conversations set title = ? where id = ?", (again(title, place), cid))
        out["conversations"] += 1
    for cid, seq, q, a in con.execute("select conversation_id, seq, question, answer from turns").fetchall():
        place = _place("turns", (cid, seq), "turn")
        con.execute(
            "update turns set question = ?, answer = ? where conversation_id = ? and seq = ?",
            (again(q, place), again(a, place), cid, seq),
        )
        out["turns"] += 1
    for rid, state in con.execute("select run_id, state from assistant_runs").fetchall():
        place = _place("assistant_runs", rid, "state")
        con.execute("update assistant_runs set state = ? where run_id = ?", (again(state, place), rid))
        out["assistant_runs"] += 1
    if _has(con, "operonx_agents_items"):
        for sid, seq, item in con.execute("select session_id, seq, item from operonx_agents_items").fetchall():
            place = _place("chat", sid, "item")  # crypto.SealedSession's place
            raw = json.loads(item)
            inner = (
                crypto.open_(raw["sealed"], place) if set(raw) == {"sealed"} else json.dumps(raw, ensure_ascii=False)
            )
            new = json.dumps({"sealed": crypto.seal(inner, place)}, ensure_ascii=False)
            con.execute("update operonx_agents_items set item = ? where session_id = ? and seq = ?", (new, sid, seq))
            out["operonx_agents_items"] += 1
    return out

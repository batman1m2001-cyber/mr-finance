"""Conversations on the server (A3, assistant.md §5, ADR-0027): listed, resumed on another device, deleted.

``assistant.db`` beside the state file (WAL), apart from the business data:

- ``conversations``: id, owner, role, client, title, created, updated, turns; a session's name (generated while
  ``title_auto``, else the person's), ``archived`` (when it left the list), its ``goal`` and context ``summary``
  (SESSIONS_PLAN.md, OWN-SS-01…06).
- ``turns``: what the panel showed, in order — the question and the answer as sent — to draw it again anywhere.
  Written when the turn starts (``running``, with each step as it ends) and completed when it ends, so a refresh
  mid-answer finds the question and the tools that ran (``interrupted``).
- ``operonx_agents_items``: the model's side (operonx-agents' ``SQLiteSession``, one shared connection per file):
  what it was sent and what it said, one session per mode (``read``: a model allowed to read client data;
  ``template``: the scrubbed question and the tools' statuses). When a prompt passes the budget
  (``ContextPolicy``), older exchanges become a summary item; nothing is deleted.
- ``assistant_runs``: a run's state while it runs or waits on a write (operonx-agents' run state), with its
  session; deleted when the run ends (it holds the whole conversation).

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

TITLE = 80  # characters of a title at most
STALE_S = 80.0  # a turn still ``running`` after this long was cut (the run's wall clock is 60 s + 5)
CUT = "Bị ngắt giữa chừng (trang được tải lại hoặc mất kết nối); các bước đã chạy ở trên. Hãy hỏi lại nếu cần."
SCHEMA = """
create table if not exists conversations (id text primary key, owner text not null, role text not null,
    client_id text, title text, created real not null, updated real not null, turns integer not null default 0);
create index if not exists conversations_owner on conversations (owner, role, updated);
create table if not exists turns (conversation_id text not null, seq integer not null, at real not null,
    question text, answer text not null, primary key (conversation_id, seq));
create table if not exists assistant_runs (run_id text primary key, state text not null, updated real not null,
    session_id text);
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
            if "session_id" not in {r[1] for r in con.execute("pragma table_info(assistant_runs)")}:  # A3's
                con.execute("alter table assistant_runs add column session_id text")
            have = {r[1] for r in con.execute("pragma table_info(conversations)")}
            added = (("title_auto", "integer not null default 1"), ("archived", "real"), ("goal", "text"),
                     ("summary", "text"), ("summary_at", "real"), ("described", "integer"))  # sessions  # fmt: skip
            for col, kind in added:
                if col not in have:
                    con.execute(f"alter table conversations add column {col} {kind}")
            if "status" not in {r[1] for r in con.execute("pragma table_info(turns)")}:
                con.execute("alter table turns add column status text")  # null: a turn written whole (before S1)
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
    title = local_title(question)
    with db() as con:
        con.execute(
            "insert into conversations (id, owner, role, client_id, title, created, updated, turns) "
            "values (?, ?, ?, ?, ?, ?, ?, 0)",
            (cid, owner(ctx), ctx.role, ctx.client_id, crypto.seal(title, _place("conversations", cid, "title")),
             now, now),
        )  # fmt: skip
    return cid


def local_title(question: Optional[str], most: int = 48) -> str:
    """A title without a model: the question's first clause, cut at a word (template mode, no model, or until the
    model's title arrives)."""
    text = " ".join(str(question or "").split())
    for stop in ("? ", ". ", "! ", "; "):
        if stop in text:
            text = text.split(stop)[0] + stop.strip()
            break
    if len(text) > most:
        text = text[:most].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    return text or "Cuộc trò chuyện"


def _seal(text: Optional[str], cid: str, column: str) -> Optional[str]:
    return None if text is None else crypto.seal(text, _place("conversations", cid, column))


def rename(ctx: Ctx, cid: str, title: str) -> Dict[str, Any]:
    """The person names the session: kept from now on (``title_auto`` = 0)."""
    c = own(ctx, cid)
    name = " ".join(str(title or "").split())[:TITLE]
    if not name:
        raise ValueError("Tên cuộc trò chuyện không được để trống")
    with db() as con:
        con.execute("update conversations set title = ?, title_auto = 0 where id = ?", (_seal(name, c["id"], "title"),
                    c["id"]))  # fmt: skip
    return own(ctx, cid)


def set_archived(ctx: Ctx, cid: str, on: bool) -> Dict[str, Any]:
    """Archive (out of the list and the resume; still opened, searched and kept) or bring back."""
    c = own(ctx, cid)
    with db() as con:
        con.execute("update conversations set archived = ? where id = ?", (time.time() if on else None, c["id"]))
    return own(ctx, cid)


def describe(cid: str, title: Optional[str] = None, goal: Optional[str] = None, summary: Optional[str] = None,
             at: Optional[int] = None) -> None:  # fmt: skip
    """What the session is about, from the model (S2, S3): a generated title replaces only a generated one; ``at``,
    the turn count it was written at (asked again at the same count, nothing is spent)."""
    with db() as con:
        if at is not None:
            con.execute("update conversations set described = ? where id = ?", (int(at), cid))
        if title:
            con.execute("update conversations set title = ? where id = ? and title_auto = 1",
                        (_seal(title[:TITLE], cid, "title"), cid))  # fmt: skip
        if goal:
            con.execute("update conversations set goal = ? where id = ?", (_seal(goal, cid, "goal"), cid))
        if summary:
            con.execute("update conversations set summary = ?, summary_at = ? where id = ?",
                        (_seal(summary, cid, "summary"), time.time(), cid))  # fmt: skip


def own(ctx: Ctx, cid: Optional[str]) -> Dict[str, Any]:
    """The conversation, when it is this person's in this role; else ValueError."""
    with db() as con:
        row = con.execute("select * from conversations where id = ?", (str(cid or ""),)).fetchone()
    if row is None or row["owner"] != owner(ctx) or row["role"] != ctx.role:
        raise ValueError("Không có cuộc trò chuyện này")
    return _row(row)


def _row(row: sqlite3.Row) -> Dict[str, Any]:
    out = dict(row)
    for col in ("title", "goal", "summary"):
        if out.get(col) is not None:
            out[col] = crypto.open_(out[col], _place("conversations", out["id"], col))
    out.pop("owner", None)
    return out


def listing(ctx: Ctx, limit: int = 50, archived: bool = False) -> List[Dict[str, Any]]:
    """The person's sessions in this role, newest first: the active ones, or the archived ones."""
    which = "archived is not null" if archived else "archived is null"
    with db() as con:
        rows = con.execute(
            f"select * from conversations where owner = ? and role = ? and {which} order by updated desc limit ?",
            (owner(ctx), ctx.role, int(limit)),
        ).fetchall()
    return [_row(r) for r in rows]


def begin(cid: str, question: Optional[str]) -> int:
    """A turn starting: its question kept now, the answer ``running`` (OWN-SS-03). Returns its seq."""
    return _write(cid, None, question, {"status": "running", "steps": []}, "running")


def progress(cid: str, seq: int, steps: List[Dict[str, Any]]) -> None:
    """The steps a running turn has finished so far."""
    with db() as con:
        con.execute("update turns set answer = ? where conversation_id = ? and seq = ? and status = 'running'",
                    (_seal_json({"status": "running", "steps": steps}, _place("turns", (cid, seq), "turn")), cid,
                     seq))  # fmt: skip


def interrupt(cid: str, seq: int, steps: List[Dict[str, Any]]) -> None:
    """A running turn cut before its answer (the stream closed): what had run, said so."""
    answer = {"status": "interrupted", "steps": steps, "text": CUT}
    sealed = _seal_json(answer, _place("turns", (cid, seq), "turn"))
    with db() as con:
        con.execute("update turns set answer = ?, status = 'interrupted' where conversation_id = ? and seq = ? and "
                    "status = 'running'", (sealed, cid, seq))  # fmt: skip


def record(cid: str, question: Optional[str], answer: Dict[str, Any], seq: Optional[int] = None) -> int:
    """A turn as the panel showed it — the one begun as ``seq``, or a new one; the conversation's ``updated`` and
    count move with it."""
    return _write(cid, seq, question, answer, str(answer.get("status") or "ok"))


def _write(cid: str, seq: Optional[int], question: Optional[str], answer: Dict[str, Any], status: str) -> int:
    now = time.time()
    with db() as con:
        con.execute("begin immediate")
        if seq is None or not con.execute("select 1 from turns where conversation_id = ? and seq = ?",
                                          (cid, seq)).fetchone():  # fmt: skip
            (seq,) = con.execute(
                "select coalesce(max(seq), -1) + 1 from turns where conversation_id = ?", (cid,)
            ).fetchone()
            place = _place("turns", (cid, seq), "turn")
            con.execute(
                "insert into turns (conversation_id, seq, at, question, answer, status) values (?, ?, ?, ?, ?, ?)",
                (cid, seq, now, crypto.seal(question, place) if question else None, _seal_json(answer, place),
                 status),
            )  # fmt: skip
            con.execute("update conversations set updated = ?, turns = turns + 1 where id = ?", (now, cid))
        else:
            con.execute("update turns set answer = ?, status = ? where conversation_id = ? and seq = ?",
                        (_seal_json(answer, _place("turns", (cid, seq), "turn")), status, cid, seq))  # fmt: skip
            con.execute("update conversations set updated = ? where id = ?", (now, cid))
        con.execute("commit")
    return seq


def archive(ctx: Ctx) -> Iterator[Dict[str, Any]]:
    """Every turn of the person's conversations in this role, opened, with its conversation's id and title: one
    query for the archive search (memory.search_history)."""
    with db() as con:
        rows = con.execute(
            "select c.id cid, c.title, t.seq, t.at, t.question, t.answer from conversations c"
            " join turns t on t.conversation_id = c.id where c.owner = ? and c.role = ?",
            (owner(ctx), ctx.role),
        ).fetchall()
    titles: Dict[str, str] = {}
    for r in rows:
        cid = r["cid"]
        if cid not in titles:
            titles[cid] = crypto.open_(r["title"], _place("conversations", cid, "title"))
        place = _place("turns", (cid, r["seq"]), "turn")
        yield {"conversation_id": cid, "title": titles[cid], "seq": r["seq"], "at": r["at"],
               "question": crypto.open_(r["question"], place), "answer": _open_json(r["answer"], place)}  # fmt: skip


def turns_of(cid: str) -> List[Dict[str, Any]]:
    with db() as con:
        rows = con.execute("select * from turns where conversation_id = ? order by seq", (cid,)).fetchall()
    out = []
    now = time.time()
    for r in rows:
        place = _place("turns", (cid, r["seq"]), "turn")
        answer = _open_json(r["answer"], place) or {}
        status = r["status"] or answer.get("status") or "ok"
        if status == "running" and now - r["at"] > STALE_S:  # the server stopped mid-turn: nothing will finish it
            status = "interrupted"
            answer = {**answer, "status": status, "text": CUT}
        out.append({"seq": r["seq"], "at": r["at"], "question": crypto.open_(r["question"], place), "answer": answer,
                    "status": status})  # fmt: skip
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
    con.execute("delete from assistant_runs where session_id like ?", (session_id(cid, "%"),))
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
                "insert or replace into assistant_runs values (?, ?, ?, ?)",
                (
                    state.run_id,
                    crypto.seal(text, _place("assistant_runs", state.run_id, "state")),
                    time.time(),
                    state.session_id,
                ),
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
        "select goal from conversations",
        "select summary from conversations",
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

    for cid, title, goal, summary in con.execute("select id, title, goal, summary from conversations").fetchall():
        con.execute(
            "update conversations set title = ?, goal = ?, summary = ? where id = ?",
            (again(title, _place("conversations", cid, "title")), again(goal, _place("conversations", cid, "goal")),
             again(summary, _place("conversations", cid, "summary")), cid),
        )  # fmt: skip
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

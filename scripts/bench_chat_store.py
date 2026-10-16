"""Chat storage on this host (ASSISTANT_PLAN A0, decision A-D2): is SQLite fit for the conversations?

Measures what the assistant would do, with operonx-agents' own `SQLiteSession` (WAL, one connection, writes
serialised): N conversations at once in one event loop, each turn reading its last 40 items and appending the
turn's items (a question, a tool call and its result, an answer: ~2 KB). Reported per N: turns per second and the
storage time of one turn (p50, p95, p99), the file's size, and an archive search (FTS5) over every message.

A second run puts the same chat writes in the app's state file, in its rollback-journal mode, beside a writer that
holds the app's `begin immediate` the way the business writes do — the "no separate store" alternative.

    .venv/bin/python scripts/bench_chat_store.py --out /tmp/chat-bench
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sqlite3
import string
import threading
import time
from pathlib import Path

from operonx_agents import SQLiteSession

WORDS = "tài sản ròng dòng tiền tháng này mục tiêu học phí nghỉ hưu rủi ro thị trường lãi suất vàng cổ phiếu".split()


def text(n: int) -> str:
    rnd = random.Random(n)
    return " ".join(rnd.choice(WORDS) for _ in range(n // 6))


def turn_items(i: int) -> list:
    return [
        {"role": "user", "content": text(120 + i % 50)},
        {"role": "assistant", "content": None, "tool_calls": [{"id": f"c{i}", "type": "function",
                                                                "function": {"name": "tong_quan", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": f"c{i}", "content": text(900)},
        {"role": "assistant", "content": text(500)},
    ]  # fmt: skip


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * p))] if xs else None


def shared_session(session_id: str, path: Path, first: list) -> SQLiteSession:
    """A session on one connection shared by every session on the file. `SQLiteSession(id, path)` opens its own
    connection each time; 50 conversations writing at once then fail with "database is locked" (4 of 1000 turns
    here, p95 1.4 s, against none and 0.56 s shared) — fixed upstream in A3."""
    if not first:
        first.append(SQLiteSession(session_id, path))
        return first[0]
    s = SQLiteSession.__new__(SQLiteSession)
    s.session_id, s._db = session_id, first[0]._db
    return s


async def sessions_run(path: Path, n: int, turns: int) -> dict:
    """``n`` conversations, ``turns`` turns each, all at once; a person takes ~2 s between turns, here none."""
    times = []
    first: list = []

    async def one(k: int):
        s = shared_session(f"user{k}:s1", path, first)
        for t in range(turns):
            t0 = time.perf_counter()
            await s.get_items(limit=40)
            await s.add_items(turn_items(t))
            times.append(time.perf_counter() - t0)

    t0 = time.perf_counter()
    await asyncio.gather(*(one(k) for k in range(n)))
    wall = time.perf_counter() - t0
    return {
        "conversations": n,
        "turns": n * turns,
        "turns_per_s": round(n * turns / wall, 1),
        "turn_store_ms_p50": round(pct(times, 0.5) * 1000, 2),
        "turn_store_ms_p95": round(pct(times, 0.95) * 1000, 2),
        "turn_store_ms_p99": round(pct(times, 0.99) * 1000, 2),
    }


def archive_search(path: Path) -> dict:
    """Every stored message into an FTS5 index (what archive memory would keep), then searches."""
    con = sqlite3.connect(path)
    con.execute("create virtual table if not exists archive using fts5(session_id unindexed, content)")
    t0 = time.perf_counter()
    rows = con.execute("select session_id, item from operonx_agents_items").fetchall()
    con.executemany(
        "insert into archive values (?, ?)",
        ((sid, json.loads(item).get("content") or "") for sid, item in rows),
    )
    con.commit()
    build = time.perf_counter() - t0
    times = []
    for q in ("học phí", "lãi suất vàng", "nghỉ hưu", "cổ phiếu rủi ro"):
        for _ in range(5):
            t0 = time.perf_counter()
            con.execute(
                "select session_id, snippet(archive, 1, '[', ']', '…', 8) from archive "
                "where archive match ? and session_id = ? order by rank limit 10",
                (f'"{q}"', "user7:s1"),
            ).fetchall()
            times.append(time.perf_counter() - t0)
    con.close()
    return {"messages": len(rows), "index_build_s": round(build, 2), "search_ms_p95": round(pct(times, 0.95) * 1000, 2)}


def shared_state_run(path: Path, n: int, turns: int) -> dict:
    """The alternative: the chat in the app's own file and mode (rollback journal), a connection per write as
    `control.db.tx` makes, beside a business writer holding `begin immediate` ~5 ms every 50 ms."""
    con = sqlite3.connect(path, isolation_level=None)
    con.execute(
        "create table if not exists chat (session_id text, seq integer, item text, primary key (session_id, seq))"
    )
    con.execute("create table if not exists business (k integer primary key, v text)")
    con.close()
    stop = threading.Event()

    def business():
        i = 0
        while not stop.is_set():
            c = sqlite3.connect(path, timeout=10, isolation_level=None)
            c.execute("begin immediate")
            c.execute("insert or replace into business values (?, ?)", (i % 1000, "x" * 2000))
            time.sleep(0.005)
            c.execute("commit")
            c.close()
            i += 1
            time.sleep(0.05)

    bg = threading.Thread(target=business)
    bg.start()
    times = []

    def one(k: int):
        for t in range(turns):
            t0 = time.perf_counter()
            c = sqlite3.connect(path, timeout=10, isolation_level=None)
            c.execute("select item from chat where session_id = ? order by seq desc limit 40", (f"u{k}",)).fetchall()
            c.execute("begin immediate")
            top = c.execute("select coalesce(max(seq), 0) from chat where session_id = ?", (f"u{k}",)).fetchone()[0]
            c.executemany(
                "insert into chat values (?, ?, ?)",
                [(f"u{k}", top + j + 1, json.dumps(it, ensure_ascii=False)) for j, it in enumerate(turn_items(t))],
            )
            c.execute("commit")
            c.close()
            times.append(time.perf_counter() - t0)

    t0 = time.perf_counter()
    workers = [threading.Thread(target=one, args=(k,)) for k in range(n)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    wall = time.perf_counter() - t0
    stop.set()
    bg.join()
    return {
        "conversations": n,
        "turns_per_s": round(n * turns / wall, 1),
        "turn_store_ms_p50": round(pct(times, 0.5) * 1000, 2),
        "turn_store_ms_p95": round(pct(times, 0.95) * 1000, 2),
        "turn_store_ms_p99": round(pct(times, 0.99) * 1000, 2),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="a folder for the test files (deleted first)")
    ap.add_argument("--turns", type=int, default=20)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tag = "".join(random.choice(string.ascii_lowercase) for _ in range(6))
    report = {"sqlite": sqlite3.sqlite_version, "wal_session": [], "shared_state_file": []}
    for n in (10, 100, 500):
        path = out / f"chat-{tag}-{n}.db"
        report["wal_session"].append(asyncio.run(sessions_run(path, n, a.turns)))
        report["wal_session"][-1]["file_mb"] = round(path.stat().st_size / 1e6, 1)
    report["archive"] = archive_search(out / f"chat-{tag}-500.db")
    for n in (10, 100):
        report["shared_state_file"].append(shared_state_run(out / f"state-{tag}-{n}.db", n, a.turns))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

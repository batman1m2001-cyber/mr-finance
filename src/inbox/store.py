"""``external_outputs`` (BRD-RULE-LC-04): one row per package received — READY → PROCESSING → IMPORTED (with the
event and view it became) or REJECTED (with the error). The body is kept as received, with its hash."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from control import audit, db

MAX_BYTES = 512 * 1024
MAX_WAITING = 200  # READY rows: beyond this the door answers 429 (a flood is not stored)


def receive(body: bytes, signed: bool) -> str:
    """Keep a package as READY; answer only its id."""
    h = hashlib.sha256(body).hexdigest()
    now = time.time()
    with db.tx() as con:
        seq = db.next_seq(con, "inbox")
        pid = f"IN-{seq:06d}"
        con.execute(
            "insert into external_outputs values (?, 'READY', ?, ?, ?, ?, ?)",
            (pid, now, int(signed), h, body.decode("utf-8", "replace"), db.dumps({})),
        )
        audit.append(con, "zone", "inbox.receive", pid, {"hash": h, "signed": signed, "bytes": len(body)})
    return pid


def waiting() -> int:
    with db.tx() as con:
        return con.execute("select count(*) from external_outputs where status = 'READY'").fetchone()[0]


def ready() -> List[Dict[str, Any]]:
    with db.tx() as con:
        return [dict(r) for r in con.execute("select * from external_outputs where status = 'READY' order by received")]


def mark(pid: str, status: str, **data: Any) -> None:
    with db.tx() as con:
        r = con.execute("select data from external_outputs where id = ?", (pid,)).fetchone()
        merged = {**json.loads(r["data"]), **data, "at": time.time()}
        con.execute("update external_outputs set status = ?, data = ? where id = ?", (status, db.dumps(merged), pid))
        if status in ("IMPORTED", "REJECTED"):
            audit.append(con, "inbox", f"inbox.{status.lower()}", pid, data)


def recent(limit: int = 10) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute(
            "select id, status, received, signed, package_hash, data from external_outputs order by received desc "
            "limit ?",
            (limit,),
        ).fetchall()
    return [{**{k: r[k] for k in r.keys() if k != "data"}, **json.loads(r["data"])} for r in rows]


def get(pid: str) -> Optional[Dict[str, Any]]:
    with db.tx() as con:
        r = con.execute("select * from external_outputs where id = ?", (pid,)).fetchone()
    return dict(r) if r else None

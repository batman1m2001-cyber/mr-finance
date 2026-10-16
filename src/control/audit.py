"""The audit log: append-only, each row chained to the one before (BRD FR-702, §13.3).

- A trigger in the database refuses UPDATE and DELETE on ``audit_log``.
- Each row's ``hash`` covers the previous row's hash and the row itself: change one row without
  recomputing every row after it and ``verify()`` names the first broken one.
- Plain SHA-256 by default: whoever can write the database could recompute the whole chain. With
  ``AUDIT_HMAC_KEY`` set the hash is an HMAC only the key holder can produce, and once a chain has
  HMAC rows it is not allowed to go back to plain SHA-256 (§13.3).
- ``append`` takes the connection of the write it records, so the change and its log row are
  committed together or not at all (§11.4).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import time
from typing import Any, Dict, Iterable, Optional

SCHEMA = """
create table if not exists audit_log (
  seq integer primary key, ts real not null, actor text not null, action text not null,
  object text not null, alg text not null, prev_hash text not null, hash text not null, data text not null);
create trigger if not exists audit_log_no_update before update on audit_log
  begin select raise(abort, 'audit_log is append-only'); end;
create trigger if not exists audit_log_no_delete before delete on audit_log
  begin select raise(abort, 'audit_log is append-only'); end;
"""

GENESIS = "0" * 64


class AuditError(RuntimeError):
    pass


def _key() -> Optional[bytes]:
    from control import secrets

    k = secrets.get("AUDIT_HMAC_KEY") or ""  # the secret store, a file or the environment (BRD-NFR-07)
    return k.encode("utf-8") if k else None


def _digest(alg: str, prev: str, body: Dict[str, Any], key: Optional[bytes]) -> str:
    msg = (prev + json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))).encode("utf-8")
    if alg == "hmac-sha256":
        if key is None:
            raise AuditError("AUDIT_HMAC_KEY cần để tính chuỗi HMAC")
        return hmac.new(key, msg, hashlib.sha256).hexdigest()
    return hashlib.sha256(msg).hexdigest()


def append(con: sqlite3.Connection, actor: str, action: str, obj: str, data: Optional[Dict[str, Any]] = None) -> int:
    """One row, in the caller's transaction."""
    last = con.execute("select seq, alg, hash from audit_log order by seq desc limit 1").fetchone()
    key = _key()
    alg = "hmac-sha256" if key else "sha256"
    if last is not None and last[1] == "hmac-sha256" and alg != "hmac-sha256":
        raise AuditError("Chuỗi nhật ký đang dùng HMAC: không được hạ về SHA-256 (thiếu AUDIT_HMAC_KEY)")
    seq = (last[0] if last else 0) + 1
    prev = last[2] if last else GENESIS
    ts = time.time()
    payload = data or {}
    body = {"seq": seq, "ts": ts, "actor": actor, "action": action, "object": obj, "data": payload}
    h = _digest(alg, prev, body, key)
    con.execute(
        "insert into audit_log values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (seq, ts, actor, action, obj, alg, prev, h, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
    )
    return seq


def verify(con: sqlite3.Connection) -> Dict[str, Any]:
    """Walk the chain: every row's prev_hash is the row before's hash, and its hash recomputes."""
    return walk(con.execute("select * from audit_log order by seq"))


def walk(rows: Iterable[Any], prev: str = GENESIS, first: int = 1) -> Dict[str, Any]:
    """``verify`` over any run of rows (database rows, or a write-once segment's: control/worm.py) starting at
    ``first`` after a row whose hash is ``prev``."""
    key = _key()
    n = 0
    algs = set()
    for row in rows:
        n += 1
        algs.add(row["alg"])
        if row["seq"] != first + n - 1:
            return {"ok": False, "count": n, "broken_at": row["seq"], "reason": "Thiếu dòng trong chuỗi"}
        if row["prev_hash"] != prev:
            return {"ok": False, "count": n, "broken_at": row["seq"], "reason": "prev_hash không khớp dòng trước"}
        data = row["data"]
        body = {
            "seq": row["seq"],
            "ts": row["ts"],
            "actor": row["actor"],
            "action": row["action"],
            "object": row["object"],
            "data": json.loads(data) if isinstance(data, str) else data,
        }
        try:
            h = _digest(row["alg"], prev, body, key)
        except AuditError as exc:
            return {"ok": False, "count": n, "broken_at": row["seq"], "reason": str(exc)}
        if not hmac.compare_digest(h, row["hash"]):
            return {"ok": False, "count": n, "broken_at": row["seq"], "reason": "Mã băm không khớp nội dung"}
        prev = row["hash"]
    return {"ok": True, "count": n, "head": prev, "algorithms": sorted(algs), "broken_at": None, "reason": ""}


def export(con: sqlite3.Connection) -> Dict[str, Any]:
    """FR-702: the whole chain in order, with the check of it, for an auditor to keep and re-verify."""
    rows = []
    for r in con.execute("select * from audit_log order by seq"):
        rows.append(
            {k: r[k] for k in ("seq", "ts", "actor", "action", "object", "alg", "prev_hash", "hash")}
            | {"data": json.loads(r["data"])}
        )
    return {"exported": time.time(), "verify": verify(con), "genesis": GENESIS, "rows": rows}

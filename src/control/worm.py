"""The audit log kept on write-once storage (BRD-RULE-DATA-10, §13.3; BRD_REMAINING_PLAN G4, ADR-0025).

The hash chain in the database shows a row was changed, unless whoever changed it recomputed every hash after it
(anyone who can write the database can, without ``AUDIT_HMAC_KEY``). Segments close that: the ``audit_check`` job
copies the rows added since the last segment into a file that is written once and never again —

- **Written once:** the file is written in full under a temporary name, made read-only, then published by a hard
  link, which fails if the name exists: a segment is never overwritten, never appended to.
- **Chained:** a segment's header holds the SHA-256 of the segment before it and the chain hash of its last row,
  so a segment removed, replaced or edited breaks the walk.
- **Checked against the database:** every row of every segment must still be in ``audit_log`` byte for byte (its
  hash and content). A row changed after it was segmented, even with the whole chain recomputed, no longer matches.

On the demo the folder is ``audit-worm/`` next to the state file (``MF_AUDIT_WORM``: another folder, or ``off``).
At the bank the same files go to object storage with a retention lock (S3 Object Lock in compliance mode): the
lock is what makes "never again" hold against the administrator too (docs/brd/architecture/bank_migration.md).
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from control import audit

FIELDS = ("seq", "ts", "actor", "action", "object", "alg", "prev_hash", "hash")
KIND = "mr-finance audit segment"


def folder() -> Optional[Path]:
    from wealth.paths import state_path

    v = os.environ.get("MF_AUDIT_WORM", "").strip()
    if v.lower() == "off":
        return None
    return Path(v) if v else state_path().parent / "audit-worm"


def _row(r: Any) -> Dict[str, Any]:
    data = r["data"]
    return {k: r[k] for k in FIELDS} | {"data": json.loads(data) if isinstance(data, str) else data}


def segments(where: Path) -> List[Path]:
    return sorted(where.glob("audit-*.jsonl")) if where.is_dir() else []


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _line(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def write(con: sqlite3.Connection, where: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """The rows added since the last segment, as a new segment: ``{"file", "first", "last", "rows"}``, or None when
    there are none. Call it after ``verify`` passed: a segment only ever extends a chain that checks."""
    where = where or folder()
    if where is None:
        return None
    where.mkdir(parents=True, exist_ok=True)
    have = segments(where)
    prev_file, last = audit.GENESIS, 0
    if have:
        prev_file = _sha(have[-1])
        last = json.loads(have[-1].open(encoding="utf-8").readline())["last"]
    rows = [_row(r) for r in con.execute("select * from audit_log where seq > ? order by seq", (last,))]
    if not rows:
        return None
    first, end = rows[0]["seq"], rows[-1]["seq"]
    head = {
        "kind": KIND,
        "version": 1,
        "first": first,
        "last": end,
        "rows": len(rows),
        "prev_segment": prev_file,
        "chain_head": rows[-1]["hash"],
        "written": time.time(),
    }
    name = where / f"audit-{first:010d}-{end:010d}.jsonl"
    part = where / f".{name.name}.{os.getpid()}.part"
    with open(part, "x", encoding="utf-8") as f:
        f.write(_line(head) + "".join(_line(r) for r in rows))
        f.flush()
        os.fsync(f.fileno())
    os.chmod(part, 0o444)
    try:
        os.link(part, name)  # fails when the name exists: a segment is written once
    finally:
        part.unlink()
    dfd = os.open(where, os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)
    return {"file": name.name, "first": first, "last": end, "rows": len(rows)}


def verify(con: sqlite3.Connection, where: Optional[Path] = None) -> Dict[str, Any]:
    """Every segment, in order: read-only, chained to the one before, its rows a valid run of the chain, and each
    row still the same in the database. ``{"ok", "segments", "rows", "last", "broken", "reason"}``."""
    where = where or folder()
    out: Dict[str, Any] = {"ok": True, "on": where is not None, "segments": 0, "rows": 0, "last": 0}
    if where is None:
        return out | {"broken": None, "reason": ""}
    prev_file, prev_hash, last = audit.GENESIS, audit.GENESIS, 0

    def broken(path: Path, reason: str) -> Dict[str, Any]:
        return out | {"ok": False, "broken": path.name, "reason": reason}

    for path in segments(where):
        if path.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
            return broken(path, "Đoạn nhật ký ghi được (phải chỉ đọc)")
        lines = path.read_text(encoding="utf-8").splitlines()
        try:
            head, rows = json.loads(lines[0]), [json.loads(x) for x in lines[1:]]
        except (ValueError, IndexError):
            return broken(path, "Đoạn nhật ký hỏng (không đọc được)")
        if head.get("kind") != KIND or head.get("prev_segment") != prev_file:
            return broken(path, "Đoạn nhật ký không nối với đoạn trước (bị xóa, thay hoặc sửa)")
        if head["first"] != last + 1 or len(rows) != head["rows"] or head["last"] != head["first"] + len(rows) - 1:
            return broken(path, "Đoạn nhật ký thiếu hoặc thừa dòng")
        walked = audit.walk(rows, prev=prev_hash, first=head["first"])
        if not walked["ok"]:
            return broken(path, f"Dòng {walked['broken_at']}: {walked['reason']}")
        if rows[-1]["hash"] != head["chain_head"]:
            return broken(path, "Mã băm cuối đoạn không khớp phần đầu")
        stored = {
            r["seq"]: _row(r)
            for r in con.execute(
                "select * from audit_log where seq between ? and ? order by seq", (head["first"], head["last"])
            )
        }
        for r in rows:
            if stored.get(r["seq"]) != r:
                why = "đã bị xóa" if r["seq"] not in stored else "đã bị sửa sau khi ghi vào đoạn chỉ-ghi-một-lần"
                return broken(path, f"Dòng {r['seq']} trong cơ sở dữ liệu {why}")
        prev_file, prev_hash, last = _sha(path), head["chain_head"], head["last"]
        out["segments"] += 1
        out["rows"] += len(rows)
        out["last"] = last
    return out | {"broken": None, "reason": ""}

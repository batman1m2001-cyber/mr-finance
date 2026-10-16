"""Client data encrypted at rest, per column (BRD-NFR-07, BRD_REMAINING_PLAN G-D3).

AES-256-GCM, a fresh 96-bit nonce per value, and the value's place — table, row id, column — as associated data,
so a ciphertext copied to another row or column does not open. A sealed value reads
``enc:1:<key id>:<base64 nonce‖ciphertext‖tag>``.

The keys are the secret ``MF_DATA_KEYS`` (control/secrets.py): ``k2=<base64 32 bytes>,k1=<base64 32 bytes>`` — the
first seals, every one listed opens. Rotation: put the new key first, run ``scripts/rotate_keys.py`` (every sealed
value is opened and sealed again under the new key, plain ones are sealed — in place, one transaction per table),
then drop the old key. With no keys the product stores plain text (the demo before G3); a sealed value with no key
to open it is an error, never shown as text.

What is sealed (:data:`COLUMNS`, :data:`FIELDS`): every client's and dependent's name, e-mail and record; their
source systems; the holdings, profile, results and RM proposals they added; every family's run result; and inside a
run, its snapshot's families and its per-family ranking and exposure. Found by scanning a populated database for
client names and account numbers, not by guessing (docs/BRD_REMAINING_PLAN.md G3).
"""

from __future__ import annotations

import base64
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from control import secrets

PREFIX = "enc:1:"

# table, primary-key columns, sealed columns, which rows (None: all)
COLUMNS: List[Tuple[str, Tuple[str, ...], Tuple[str, ...], Optional[str]]] = [
    ("people", ("id",), ("name", "email", "data"), "kind in ('client', 'dependent')"),
    ("client_sources", ("client_id", "source"), ("data",), None),
    ("holdings", ("key",), ("data",), None),
    ("profile", ("id",), ("data",), None),
    ("results", ("client_id", "kind"), ("data",), None),
    ("reviews", ("id",), ("title", "data", "note"), None),
    ("family_impacts", ("id",), ("data",), None),
    ("rm_contacts", ("id",), ("data",), None),
]
# table, the JSON column, the fields of it sealed (the rest stays plain: SQL reads it)
FIELDS: List[Tuple[str, str, Tuple[str, ...]]] = [
    ("run_snapshots", "data", ("families",)),
    ("application_runs", "data", ("ranking", "exposure")),
]


class CryptoError(RuntimeError):
    pass


def _aesgcm():
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    return AESGCM


_KEYS: Dict[str, Any] = {}


def keys() -> List[Tuple[str, bytes]]:
    """``[(id, key)]``, the sealing one first; empty when none is set."""
    raw = secrets.get("MF_DATA_KEYS") or ""
    if _KEYS.get("raw") == raw:
        return _KEYS["parsed"]
    out = []
    for part in [p.strip() for p in raw.split(",") if p.strip()]:
        kid, _, b64 = part.partition("=")
        try:
            key = base64.b64decode(b64, validate=True)
        except ValueError:
            raise CryptoError(f"MF_DATA_KEYS: khóa {kid!r} không phải base64") from None
        if not kid.isidentifier() or len(key) != 32:
            raise CryptoError(f"MF_DATA_KEYS: khóa {kid!r} cần tên (k1, k2…) và đúng 32 byte")
        out.append((kid, key))
    _KEYS.update(raw=raw, parsed=out)
    return out


def on() -> bool:
    return bool(keys())


def current() -> Optional[str]:
    k = keys()
    return k[0][0] if k else None


def new_key() -> str:
    """A fresh key, base64 (``scripts/rotate_keys.py --new``)."""
    return base64.b64encode(os.urandom(32)).decode()


def where(table: str, row_id: Any, column: str) -> bytes:
    """The associated data: a value's place."""
    rid = "/".join(str(x) for x in row_id) if isinstance(row_id, (tuple, list)) else str(row_id)
    return f"{table}/{rid}/{column}".encode("utf-8")


def sealed(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(PREFIX)


def seal(text: Optional[str], aad: bytes) -> Optional[str]:
    """``text`` sealed under the current key; as it is when no key is set, or when it is None."""
    if text is None:
        return None
    k = keys()
    if not k or sealed(text):
        return text
    kid, key = k[0]
    nonce = os.urandom(12)
    ct = _aesgcm()(key).encrypt(nonce, str(text).encode("utf-8"), aad)
    return f"{PREFIX}{kid}:{base64.b64encode(nonce + ct).decode()}"


def open_(text: Optional[str], aad: bytes) -> Optional[str]:
    """A sealed value opened; a plain one as it is."""
    if not sealed(text):
        return text
    kid, _, b64 = text[len(PREFIX) :].partition(":")
    key = dict(keys()).get(kid)
    if key is None:
        raise CryptoError(f"không có khóa {kid!r} để mở dữ liệu (MF_DATA_KEYS)")
    raw = base64.b64decode(b64)
    try:
        return _aesgcm()(key).decrypt(raw[:12], raw[12:], aad).decode("utf-8")
    except Exception:  # noqa: BLE001 — InvalidTag: tampered, or moved from another row
        raise CryptoError(f"dữ liệu mã hóa không mở được ở {aad.decode()!r} (bị sửa hoặc chuyển chỗ)") from None


def seal_json(obj: Any, aad: bytes) -> Any:
    """A JSON field sealed as a string; the object itself when no key is set."""
    if not on() or obj is None:
        return obj
    return seal(json.dumps(obj, ensure_ascii=False, sort_keys=True), aad)


def open_json(value: Any, aad: bytes) -> Any:
    return json.loads(open_(value, aad)) if sealed(value) else value


# -- rotation ----------------------------------------------------------------------------------


def rotate(con: sqlite3.Connection) -> Dict[str, int]:
    """Every sealed value of the database opened and sealed again under the current key, every plain one sealed:
    ``{table: values written}``. Tables the database does not have are skipped. Nothing to do without a key."""
    if not on():
        raise CryptoError("chưa có khóa (MF_DATA_KEYS): không có gì để mã hóa")
    have = {r[0] for r in con.execute("select name from sqlite_master where type = 'table'")}
    kid = current()
    out: Dict[str, int] = {}
    for table, pk, cols, cond in COLUMNS:
        if table not in have:
            continue
        n = 0
        q = f"select {', '.join(pk + cols)} from {table}" + (f" where {cond}" if cond else "")
        for row in con.execute(q).fetchall():
            rid = tuple(row[: len(pk)])
            new = {}
            for c, v in zip(cols, row[len(pk) :]):
                if v is None or (sealed(v) and v[len(PREFIX) :].startswith(kid + ":")):
                    continue
                new[c] = seal(open_(v, where(table, rid, c)), where(table, rid, c))
            if new:
                sets = ", ".join(f"{c} = ?" for c in new)
                cond_pk = " and ".join(f"{c} = ?" for c in pk)
                con.execute(f"update {table} set {sets} where {cond_pk}", (*new.values(), *rid))
                n += len(new)
        out[table] = n
    for table, col, fields in FIELDS:
        if table not in have:
            continue
        n = 0
        for rid, text in con.execute(f"select id, {col} from {table}").fetchall():
            data = json.loads(text)
            changed = False
            for f in fields:
                v = data.get(f)
                if v is None or (sealed(v) and v[len(PREFIX) :].startswith(kid + ":")):
                    continue
                data[f] = seal_json(open_json(v, where(table, rid, f)), where(table, rid, f))
                changed = True
            if changed:
                con.execute(
                    f"update {table} set {col} = ? where id = ?",
                    (json.dumps(data, ensure_ascii=False, sort_keys=True), rid),
                )
                n += 1
        out[table] = n
    return out


def census(con: sqlite3.Connection) -> Dict[str, int]:
    """How many values each key seals, and how many are plain: ``{"k1": 120, "plain": 0}``. After a rotation, a key
    with nothing under it may be dropped from ``MF_DATA_KEYS``."""
    have = {r[0] for r in con.execute("select name from sqlite_master where type = 'table'")}
    out: Dict[str, int] = {}

    def count(v: Any) -> None:
        if v is None:
            return
        k = v[len(PREFIX) :].partition(":")[0] if sealed(v) else "plain"
        out[k] = out.get(k, 0) + 1

    for table, _, cols, cond in COLUMNS:
        if table in have:
            for row in con.execute(f"select {', '.join(cols)} from {table}" + (f" where {cond}" if cond else "")):
                for v in row:
                    count(v)
    for table, col, fields in FIELDS:
        if table in have:
            for (text,) in con.execute(f"select {col} from {table}"):
                data = json.loads(text)
                for f in fields:
                    v = data.get(f)
                    count(v if v is None or isinstance(v, str) else "plain")  # an object: a field stored plain
    return out


class SealedSession:
    """An operonx-agents ``Session`` whose items are sealed (the declaring chat's history, declare/ops.chat_session):
    each item is stored as ``{"sealed": "enc:1:…"}`` bound to its session, and opened when read. With no key the items
    are stored as they are."""

    def __init__(self, inner: Any, session_id: str) -> None:
        self.inner, self.session_id = inner, session_id
        self._at = where("chat", session_id, "item")

    def _seal(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {"sealed": seal_json(item, self._at)} if on() else item

    def _open(self, item: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if isinstance(item, dict) and set(item) == {"sealed"}:
            return open_json(item["sealed"], self._at)
        return item

    async def get_items(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        return [self._open(i) for i in await self.inner.get_items(limit)]

    async def add_items(self, items: List[Dict[str, Any]]) -> None:
        await self.inner.add_items([self._seal(i) for i in items])

    async def pop_item(self) -> Optional[Dict[str, Any]]:
        return self._open(await self.inner.pop_item())

    async def clear(self) -> None:
        await self.inner.clear()

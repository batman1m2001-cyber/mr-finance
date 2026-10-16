"""Where the product's keys come from (BRD-NFR-07 “khóa trong kho bí mật”, BRD_REMAINING_PLAN G-D3).

``get(name)`` looks in order:

1. **a secret store** — a Vault-compatible KV v2 store when ``VAULT_ADDR`` is set: ``GET
   {VAULT_ADDR}/v1/{VAULT_MOUNT}/data/{VAULT_PATH}`` with ``X-Vault-Token`` (``VAULT_TOKEN``, or the file
   ``VAULT_TOKEN_FILE``), the value under ``name``. Read once, kept ``VAULT_TTL`` seconds (300);
2. **a file** — ``MF_SECRETS_DIR/<name>`` (the Docker / Kubernetes secrets layout), its text stripped;
3. **the environment** — ``os.environ[name]``, for development and the public demo.

A store that is configured but does not answer is an error, never a quiet fall back to the environment: a bank that
moved its keys to Vault must not run on a stale copy left in ``.env``. :func:`source` says where a name came from
(``/healthz`` shows it, never the value).

The names: ``MF_DATA_KEYS`` (the column keys, control/crypto.py), ``AUDIT_HMAC_KEY``, ``MF_SESSION_SECRET``,
``MF_INBOX_KEY``, ``MF_ZONE_KEY``.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_CACHE: Dict[str, Any] = {}
_LOCK = threading.Lock()


class SecretStoreError(RuntimeError):
    """The secret store is configured and did not answer."""


def _vault() -> Optional[Dict[str, str]]:
    addr = (os.environ.get("VAULT_ADDR") or "").strip().rstrip("/")
    if not addr:
        return None
    ttl = float(os.environ.get("VAULT_TTL") or 300)
    with _LOCK:
        hit = _CACHE.get("vault")
        if hit and hit[0] == addr and time.time() - hit[1] < ttl:
            return hit[2]
    token = (os.environ.get("VAULT_TOKEN") or "").strip()
    if not token and os.environ.get("VAULT_TOKEN_FILE"):
        token = Path(os.environ["VAULT_TOKEN_FILE"]).read_text(encoding="utf-8").strip()
    mount = (os.environ.get("VAULT_MOUNT") or "secret").strip("/")
    path = (os.environ.get("VAULT_PATH") or "mr-finance").strip("/")
    req = urllib.request.Request(f"{addr}/v1/{mount}/data/{path}", headers={"X-Vault-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:  # noqa: S310 — the address is the operator's setting
            data = json.loads(r.read())["data"]["data"]
    except Exception as e:  # noqa: BLE001 — any failure: the store is not answering
        raise SecretStoreError(f"kho bí mật {addr} không trả lời: {type(e).__name__}") from None
    values = {str(k): str(v) for k, v in (data or {}).items()}
    with _LOCK:
        _CACHE["vault"] = (addr, time.time(), values)
    return values


def lookup(name: str) -> Tuple[Optional[str], str]:
    """``(value, source)``: source is ``vault``, ``file``, ``env`` or ``none``."""
    store = _vault()
    if store is not None and store.get(name):
        return store[name], "vault"
    folder = (os.environ.get("MF_SECRETS_DIR") or "").strip()
    if folder:
        f = Path(folder) / name
        if f.is_file():
            text = f.read_text(encoding="utf-8").strip()
            if text:
                return text, "file"
    env = (os.environ.get(name) or "").strip()
    if env:
        return env, "env"
    return None, "none"


def get(name: str, default: Optional[str] = None) -> Optional[str]:
    value, _ = lookup(name)
    return value if value is not None else default


def source(name: str) -> str:
    try:
        return lookup(name)[1]
    except SecretStoreError:
        return "error"


def clear() -> None:
    """Forget what the store said (tests; a rotation that changed the keys)."""
    with _LOCK:
        _CACHE.clear()

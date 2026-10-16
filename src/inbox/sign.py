"""HMAC-SHA256 over the exact bytes sent (header ``x-mf-signature: sha256=<hex>``). The key is ``MF_INBOX_KEY`` on
both sides; without it, packages arrive unsigned and are imported as such (the demo), and with it an unsigned or
wrongly signed package is rejected (BRD-RULE-LC-04)."""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Optional

HEADER = "x-mf-signature"


def key() -> Optional[bytes]:
    k = (os.environ.get("MF_INBOX_KEY") or "").strip()
    return k.encode("utf-8") if k else None


def sign(body: bytes, secret: Optional[bytes] = None) -> str:
    secret = secret or key()
    if not secret:
        raise ValueError("MF_INBOX_KEY is not set")
    return "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()


def valid(body: bytes, signature: Optional[str], secret: Optional[bytes] = None) -> bool:
    secret = secret or key()
    if not secret or not signature:
        return False
    return hmac.compare_digest(sign(body, secret), signature.strip())

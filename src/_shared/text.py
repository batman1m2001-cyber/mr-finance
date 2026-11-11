"""Text the way Vietnamese documents write it: accents folded away, numbers in every spelling."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional


def ascii_lower(text: str) -> str:
    """``Mã CK`` → ``ma ck``: the forms a statement's headers come in, made comparable."""
    t = unicodedata.normalize("NFD", str(text)).replace("đ", "d").replace("Đ", "D")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", t).strip().lower()


def number(value: Any) -> Optional[float]:
    """``2.000.000.000``, ``2,000,000,000``, ``5,0`` and ``1200`` as numbers; None if none."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = re.sub(r"[^\d.,-]", "", str(value))
    if not s:
        return None
    if s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3 and "," not in s):
        s = s.replace(".", "")
    if s.count(",") > 1 or (s.count(",") == 1 and len(s.split(",")[1]) == 3):
        s = s.replace(",", "")
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

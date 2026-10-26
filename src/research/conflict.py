"""Conflict of interest, as a structured field (BRD-RULE-CONTENT-02, CONTENT-03; BRD completion F8): on research and on
the newsletter. ``{related, parties, statement}`` — whether the piece concerns a party related to the bank, which, and
the disclosure the client reads. Text that names a party on the ``related_parties`` list cannot go out as
“không liên quan”: it must be declared. Shown on every piece of client content that uses the item."""

from __future__ import annotations

import re
from typing import Any, Dict, List

NONE = "Không có xung đột lợi ích cần công bố."


class ConflictError(ValueError):
    pass


def parties() -> List[str]:
    from control import config

    return list(config.data("related_parties"))


def mentions(*texts: str) -> List[str]:
    """The related parties named in ``texts`` (whole words, any case)."""
    text = " ".join(t or "" for t in texts)
    return [p for p in parties() if re.search(r"(?<!\w)" + re.escape(p) + r"(?!\w)", text, re.IGNORECASE)]


def declare(given: Any, *texts: str, covered: Any = ()) -> Dict[str, Any]:
    """The checked declaration: ``given`` is ``{related, parties, statement}`` (a legacy free-text string is its
    statement). Refused when the text names a related party and nothing is declared, or a declaration lacks the
    parties or a statement of at least 20 characters. ``covered``: parties already disclosed by what the piece quotes
    (a newsletter's sections), which need no second declaration."""
    if isinstance(given, str) or given is None:
        given = {"related": bool(str(given or "").strip()), "statement": str(given or "").strip(), "parties": []}
    if not isinstance(given, dict):
        raise ConflictError("conflict: {related, parties, statement}")
    named = mentions(*texts)
    related = bool(given.get("related"))
    done = {str(p).lower() for p in covered}
    undeclared = [p for p in named if p.lower() not in done]
    if undeclared and not related:
        raise ConflictError(
            f"Nội dung nhắc tới {', '.join(undeclared)} (bên liên quan của ngân hàng): cần khai báo xung đột lợi ích "
            "(CONTENT-03)"
        )
    out = {"related": related, "parties": [], "statement": "", "mentions": named}
    if related:
        ps = [str(p).strip() for p in (given.get("parties") or []) if str(p).strip()] or named
        statement = str(given.get("statement") or "").strip()
        if not ps:
            raise ConflictError("Khai báo xung đột lợi ích cần tên bên liên quan")
        if len(statement) < 20:
            raise ConflictError("Lời công bố xung đột lợi ích cần từ 20 ký tự")
        out.update(parties=ps[:10], statement=statement[:500])
    return out


def disclosure(c: Dict[str, Any]) -> str:
    """What the client reads."""
    if not c or not c.get("related"):
        return NONE
    return f"Công bố xung đột lợi ích ({', '.join(c['parties'])}): {c['statement']}"

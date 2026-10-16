"""The event step."""

from __future__ import annotations

from typing import Optional

from operonx import op

from control import roles
from events import store


@op
def group(news_ids: list, title: Optional[str] = None, by: str = "cio") -> dict:
    roles.require(by, "cio")
    ids = [str(i) for i in news_ids or []]
    if not ids:
        raise ValueError("Cần chọn ít nhất một tin")
    return {"event": store.create(ids, title, by)}


@op
def flag_urgent(event_id: str, urgent: bool = True, reason: str = "", by: str = "cio") -> dict:
    """POST /api/events/urgent: the CIO flags an event urgent with a reason, or takes the flag off (BRD-KPI-01)."""
    roles.require(by, "cio")
    return {"event": store.set_urgent(str(event_id or ""), bool(urgent), str(reason or ""), by)}

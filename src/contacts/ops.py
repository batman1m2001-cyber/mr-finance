"""Recording an RM's contact with a family."""

from __future__ import annotations

from typing import Optional

from operonx import op

from contacts import store
from control import roles
from people import auth


@op
def log_contact(
    family_id: str, channel: str = "call", signal: Optional[str] = None, note: str = "", by: str = None
) -> dict:
    """POST /api/rm/contacts: an RM records a contact with a family assigned to them, and the signal it started
    from, or none (BRD-KPI-06)."""
    roles.require(by, "rm")
    family_id = str(family_id or "")
    auth.require_client(family_id)  # only a family assigned to this RM (ROLE-02)
    return {"contact": store.log(family_id, str(channel or ""), signal or None, str(note or ""), by)}

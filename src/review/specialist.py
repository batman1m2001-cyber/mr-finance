"""The certified specialist (BRD-RULE-ROLE-05 “approves action recommendations for assigned families”, WF-08 step 8
“approve action recommendations, if any”; BRD_REMAINING_PLAN G8, G-D7).

- **An action recommendation** is an item of the RM queue (FEAT-27): an option the client sent from Kế hoạch, or a
  recommendation the RM writes for the family (``rm_note``). Both carry actions.
- **Who approves.** A family's specialists are its team's leads (people/store.py ``teams``). Those holding a
  certificate in force (configuration ``certifications``, owned by Compliance, two people) approve. When the RM
  approves an item of a family that has one, it waits for the specialist (``pending_specialist``); the client sees
  it only once a specialist approved it. A family with none: the RM approves alone, as the BRD's “if any” allows.
- The certificate is checked again when the specialist decides: one that lapsed in between cannot approve.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from control import config


def certificate(person_id: str, today: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """The specialist's certificate when it is in force ``today``."""
    c = config.data("certifications").get(str(person_id or ""))
    if not c or date.fromisoformat(c["valid_until"]) < (today or date.today()):
        return None
    return c


def approvers(client_id: str, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """The certified specialists assigned to the family, with their certificate."""
    from people import store

    out = []
    for sid in store.specialists_of(client_id):
        c = certificate(sid, today)
        if c:
            p = store.person(sid) or {}
            out.append({"id": sid, "name": p.get("name", sid), "title": p.get("title", ""), **c})
    return out

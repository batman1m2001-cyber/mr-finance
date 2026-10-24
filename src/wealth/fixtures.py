"""The read-only demo data: the market on the demo date, and the clients (read from the people table, seeded
from data/clients/)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, List

from wealth.paths import DATA


@lru_cache(maxsize=1)
def market() -> Dict[str, Any]:
    return json.loads((DATA / "market.json").read_text(encoding="utf-8"))


def client(client_id: str) -> Dict[str, Any]:
    """One client's record (a copy: callers may change it), from the people table (src/people). Inside a request,
    only to someone who may see that family (src/people/auth.py: the family, its RM, CIO, Admin)."""
    from people import auth, store

    auth.require_client(client_id)
    return store.client(client_id)


def client_ids(members: bool = False) -> List[str]:
    """Every client, sorted; household members (a spouse) only with ``members=True``."""
    from people import store

    return store.client_ids(members)


def summary(client_id: str) -> Dict[str, Any]:
    """What the client picker shows."""
    c = client(client_id)
    return {k: c.get(k) for k in ("id", "name", "age", "occupation", "segment", "persona_hint", "city")}


@lru_cache(maxsize=1)
def factors() -> Dict[str, Any]:
    """The policies, macro moves and infrastructure projects the alerts watch (data/factors.json)."""
    return json.loads((DATA / "factors.json").read_text(encoding="utf-8"))

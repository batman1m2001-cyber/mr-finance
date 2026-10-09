"""The read-only demo data: the market on the demo date and the sample clients."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Dict, List

from wealth.paths import DATA


@lru_cache(maxsize=1)
def market() -> Dict[str, Any]:
    return json.loads((DATA / "market.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=32)
def _client(client_id: str) -> Dict[str, Any]:
    path = DATA / "clients" / f"{client_id}.json"
    if not path.is_file():
        raise KeyError(f"no client {client_id!r}")
    return json.loads(path.read_text(encoding="utf-8"))


def client(client_id: str) -> Dict[str, Any]:
    """One client's fixture (a copy: callers may change it)."""
    return json.loads(json.dumps(_client(client_id)))


def client_ids(members: bool = False) -> List[str]:
    """Every client, sorted; household members (a spouse) only with ``members=True``."""
    out = []
    for path in sorted((DATA / "clients").glob("*.json")):
        c = _client(path.stem)
        if members or not c.get("member_of"):
            out.append(path.stem)
    return out


def summary(client_id: str) -> Dict[str, Any]:
    """What the client picker shows."""
    c = _client(client_id)
    return {
        k: c.get(k) for k in ("id", "name", "age", "occupation", "segment", "persona_hint", "city")
    }

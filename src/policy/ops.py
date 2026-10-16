"""The policy radar's served steps (FR-306): Compliance adds, verifies, updates and summarises a document."""

from __future__ import annotations

import asyncio
from typing import Optional

from operonx import op

from policy import agent, store


@op
async def add(item: dict, by: str) -> dict:
    """POST /api/policy: a document from the Official Gazette (fetched) or an official page (pasted)."""
    return {"document": await asyncio.to_thread(store.add, item, by)}


@op
def verify(document_id: str, by: str, note: str = "") -> dict:
    """POST /api/policy/verify: a second Compliance person confirms the source."""
    return {"document": store.verify(document_id, by, note)}


@op
def set_status(document_id: str, status: str, by: str, note: str = "", date: Optional[str] = None) -> dict:
    """POST /api/policy/status: where the document stands now."""
    return {"document": store.set_status(document_id, status, by, note, date or "")}


@op
async def summarise(document_id: str, by: str, mode: str = "") -> dict:
    """POST /api/policy/summarise: the policy agent on a verified document."""
    return {"document": await agent.summarise(document_id, by, mode)}

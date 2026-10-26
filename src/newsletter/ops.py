"""The newsletter's served steps (FR-801): a CIO drafts, edits, submits or withdraws; another CIO approves or
returns."""

from __future__ import annotations

from typing import Optional

from operonx import op

from newsletter import store


@op
async def draft(
    view_ids: list,
    by: str,
    title: str = "",
    mode: str = "template",
    distribution: Optional[dict] = None,
    conflict: Optional[dict] = None,
    body: str = "",
) -> dict:
    """POST /api/newsletters: a draft from approved views, or the CIO's own article (a body)."""
    return {"newsletter": await store.draft(view_ids, by, title, mode, distribution, conflict, body)}


@op
def act(newsletter_id: str, action: str, by: str, note: str = "", changes: Optional[dict] = None) -> dict:
    """POST /api/newsletters/act: edit, submit, approve, return or withdraw."""
    return {"newsletter": store.act(newsletter_id, action, by, note, changes)}

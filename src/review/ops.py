"""Proposing to the RM, and the RM's decision."""

from __future__ import annotations

from operonx import op

from wealth import fixtures, store


@op
def read_proposal(
    client_id: str = None, scenario: str = None, title: str = None, option: dict = None, summary: list = None
) -> dict:
    """A simulation's option, checked (``option``: {"id", "title", "actions", "effect"}), as the
    queue item it becomes."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    option = option or {}
    if option.get("id") not in ("light", "heavy"):
        raise ValueError("option.id is light or heavy")
    return {
        "client_id": client_id,
        "kind": str(scenario or "scenario"),
        "title": f"{title or 'Kịch bản'} — {option.get('title') or option['id']}",
        "data": {"scenario": scenario, "option": option, "summary": summary or []},
    }


@op
def propose(client_id: str, kind: str, title: str, data: dict) -> dict:
    """Into the queue, pending."""
    item_id = store.propose(client_id, kind, title, data)
    return {"item": store.review(item_id)}


@op
def read_decision(item_id: str = None, decision: str = None, note: str = None) -> dict:
    """The RM's decision, checked: approved or rejected, with a note of at most 1000 characters."""
    decision = str(decision or "")
    if decision not in ("approved", "rejected"):
        raise ValueError("decision is approved or rejected")
    return {"item_id": str(item_id or ""), "decision": decision, "note": str(note or "")[:1000]}


@op
def check_pending(item_id: str) -> dict:
    """The item exists and still waits."""
    found = store.review(item_id)
    if not found:
        raise ValueError(f"no review item {item_id!r}")
    if found["status"] != "pending":
        raise ValueError(f"{item_id} was already {found['status']}")
    return {"item_id": item_id}


@op
def decide(item_id: str, decision: str, note: str = "") -> dict:
    """The RM's decision, kept with its note and time."""
    return {"item": store.decide(item_id, decision, note)}

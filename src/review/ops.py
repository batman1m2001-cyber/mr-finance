"""Proposing to the RM, and the RM's decision."""

from __future__ import annotations

from operonx import op

from wealth import fixtures, store


@op
def read_proposal(item: dict = None) -> dict:
    """``{"client_id", "scenario", "title", "option": {"id", "title", "actions", "effect"}, "summary"?}``."""
    item = item or {}
    client_id = str(item.get("client_id") or "")
    if client_id not in fixtures.client_ids(members=True):
        raise ValueError(f"no client {client_id!r}")
    option = item.get("option") or {}
    if option.get("id") not in ("light", "heavy"):
        raise ValueError("option.id is light or heavy")
    return {
        "client_id": client_id,
        "kind": str(item.get("scenario") or "scenario"),
        "title": f"{item.get('title') or 'Kịch bản'} — {option.get('title') or option['id']}",
        "data": {"scenario": item.get("scenario"), "option": option, "summary": item.get("summary") or []},
    }


@op
def propose(client_id: str, kind: str, title: str, data: dict) -> dict:
    """Into the queue, pending."""
    item_id = store.propose(client_id, kind, title, data)
    return {"item": store.review(item_id)}


@op
def read_decision(item: dict = None) -> dict:
    """``{"item_id", "decision": "approved" | "rejected", "note"?}``."""
    item = item or {}
    decision = str(item.get("decision") or "")
    if decision not in ("approved", "rejected"):
        raise ValueError("decision is approved or rejected")
    return {"item_id": str(item.get("item_id") or ""), "decision": decision, "note": str(item.get("note") or "")[:1000]}


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

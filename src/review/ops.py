"""Proposing to the RM, and the RM's decision. The RM's approval stands alone: there is no specialist step since
OWN-FB-18 (the BRD's WF-08 “if any”)."""

from __future__ import annotations

from operonx import op

from control import roles
from control.errors import BadRequest
from people import auth
from wealth import fixtures, store


@op
def read_proposal(
    client_id: str = None, scenario: str = None, title: str = None, option: dict = None, summary: list = None
) -> dict:
    """A simulation's option, checked (``option``: {"id", "title", "actions", "effect"}), as the
    queue item it becomes."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise BadRequest(f"no client {client_id!r}")
    auth.require_client(client_id)  # their family, their RM, or the desk (ROLE-02)
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
def read_decision(item_id: str = None, decision: str = None, note: str = None, by: str = None) -> dict:
    """The RM's decision, checked: by an RM, approved or rejected, with a note of at most 1000 characters."""
    roles.require(by, "rm")
    decision = str(decision or "")
    if decision not in ("approved", "rejected"):
        raise ValueError("decision is approved or rejected")
    return {"item_id": str(item_id or ""), "decision": decision, "note": str(note or "")[:1000], "by": by}


@op
def check_pending(item_id: str) -> dict:
    """The item exists and still waits."""
    found = store.review(item_id)
    if not found:
        raise ValueError(f"no review item {item_id!r}")
    auth.require_client(found["client_id"])  # an RM decides only for the families assigned to them (ROLE-02)
    if found["status"] not in ("pending", "pending_specialist"):  # the second: queued for an expert before OWN-FB-18
        raise ValueError(f"{item_id} was already {found['status']}")
    return {"item_id": item_id}


@op
def decide(item_id: str, decision: str, note: str = "", by: str = None) -> dict:
    """The RM's decision, kept with its note, its time and who decided, and audited (BRD-KPI-05)."""
    return {"item": store.decide(item_id, decision, note, by)}


@op
def recommend(client_id: str = None, title: str = None, actions: list = None, note: str = None, by: str = None) -> dict:
    """POST /api/review/recommend: the RM writes an action recommendation for a family assigned to them (G-D7); the
    RM's own approval stands."""
    roles.require(by, "rm")
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise BadRequest(f"no client {client_id!r}")
    auth.require_client(client_id)
    title = str(title or "").strip()[:200]
    acts = [str(a).strip()[:300] for a in (actions or []) if str(a).strip()][:10]
    if not title or not acts:
        raise BadRequest("Khuyến nghị cần tiêu đề và ít nhất một việc cần làm")
    item_id = store.propose(client_id, "rm_note", title, {"option": {"title": title, "actions": acts}, "author": by})
    return {"item": store.decide(item_id, "approved", str(note or "")[:1000], by)}

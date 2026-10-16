"""Proposing to the RM, the RM's decision, and the certified specialist's (G8, review/specialist.py)."""

from __future__ import annotations

from operonx import op

from control import roles
from control.errors import BadRequest, Conflict
from people import auth
from review import specialist
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
    if found["status"] != "pending":
        raise ValueError(f"{item_id} was already {found['status']}")
    return {"item_id": item_id}


@op
def decide(item_id: str, decision: str, note: str = "", by: str = None) -> dict:
    """The RM's decision, kept with its note, its time and who decided, and audited (BRD-KPI-05). An approval of a
    family with a certified specialist waits for them (BRD-RULE-WF-08)."""
    status = decision
    if decision == "approved":
        found = store.review(item_id)
        if found and specialist.approvers(found["client_id"]):
            status = "pending_specialist"
    return {"item": store.decide(item_id, status, note, by)}


@op
def specialist_decide(item_id: str = None, decision: str = None, note: str = None, by: str = None) -> dict:
    """POST /api/review/specialist: a certified specialist assigned to the family approves or rejects an action
    recommendation the RM approved (BRD-RULE-ROLE-05, WF-08). A rejection says why."""
    roles.require(by, "specialist")
    item_id, decision, note = str(item_id or ""), str(decision or ""), str(note or "").strip()[:1000]
    if decision not in ("approved", "rejected"):
        raise BadRequest("decision là approved hoặc rejected")
    if decision == "rejected" and len(note) < 10:
        raise BadRequest("Từ chối cần lý do từ 10 ký tự")
    found = store.review(item_id)
    if not found:
        raise BadRequest(f"không có đề xuất {item_id}")
    auth.require_client(found["client_id"])  # only a family assigned to this specialist
    if by not in {a["id"] for a in specialist.approvers(found["client_id"])}:
        raise roles.Forbidden("Chỉ chuyên gia được giao gia đình này, có chứng chỉ còn hiệu lực, mới duyệt được")
    done = store.move(
        item_id,
        "pending_specialist",
        decision,
        by,
        "review.specialist",
        {"specialist_by": by, "specialist_note": note, "certificate": specialist.certificate(by)["certificate"]},
        audit_data={"decision": decision},
    )
    if done is None:
        raise Conflict(f"{item_id} không chờ chuyên gia duyệt (đang {found['status']})")
    return {"item": done}


@op
def recommend(client_id: str = None, title: str = None, actions: list = None, note: str = None, by: str = None) -> dict:
    """POST /api/review/recommend: the RM writes an action recommendation for a family assigned to them (G-D7). It
    waits for the family's certified specialist; with none, the RM's own approval stands (the BRD's “if any”)."""
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
    to = "pending_specialist" if specialist.approvers(client_id) else "approved"
    return {"item": store.decide(item_id, to, str(note or "")[:1000], by)}

"""The research and goal-branch steps (FR-201…204, FR-601…604)."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from operonx import op

from control import roles
from procedural import goals
from research import store
from wealth import fixtures


@op
def upload(item: dict, by: str) -> dict:
    """A report, house view or regulation note, waiting for Compliance."""
    roles.require(by, "cio")
    return {"item": store.upload(item or {}, by)}


@op
def release(item_id: str, decision: str, by: str, note: str = "") -> dict:
    """Compliance releases (after the release time) or rejects, with a note."""
    roles.require(by, "compliance")
    return {"item": store.decide(str(item_id), str(decision), by, note)}


@op
def declare_outflow(family_id: str, goal_id: str, purpose: str, by: str, country: str = "") -> dict:
    """The RM records where a goal's money goes (FR-601)."""
    roles.require(by, "rm")
    if family_id not in fixtures.client_ids():
        raise ValueError(f"không có gia đình {family_id}")
    if goal_id not in {g["goal_id"] for g in goals.goals_of(fixtures.client(family_id), date.today())}:
        raise ValueError(f"không có mục tiêu {goal_id} đang hoạt động")
    return {"declared": store.declare(family_id, goal_id, purpose, country, by)}


def matches(family_id: Optional[str] = None, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """Released regulation notes × active goals (computed on read: deterministic, from what is kept)."""
    ids = [family_id] if family_id else fixtures.client_ids()
    fams = {fid: fixtures.client(fid) for fid in ids}
    return goals.match(store.released_notes(), fams, store.declared(), today or date.today())

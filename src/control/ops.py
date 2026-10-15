"""Configuration changes as served steps (FR-701): propose, then approve or reject."""

from __future__ import annotations

from operonx import op

from control import config


@op
def propose(kind: str = None, data=None, by: str = None, note: str = "") -> dict:
    """A user of the owner's role proposes a new version (checked; the version in force is unchanged)."""
    return {"version": config.propose(str(kind or ""), data, str(by or ""), note or "")}


@op
def decide(version_id: str = None, action: str = None, by: str = None, note: str = "") -> dict:
    """A user of the owner's role approves (it comes into force) or rejects; two people where §13.1 says so."""
    return {"version": config.decide(str(version_id or ""), str(action or ""), str(by or ""), note or "")}

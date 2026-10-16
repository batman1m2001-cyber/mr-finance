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


@op
def check_chain(tick: int = None, at: str = None) -> dict:
    """The ``audit_check`` job: walk the audit chain; broken raises an alert for Compliance and Admin, whole again
    resolves it (BRD-NFR-12)."""
    from control import alerts, db, log
    from control.audit import verify

    with db.tx() as con:
        got = verify(con)
    if got["ok"]:
        alerts.resolve("audit_chain", "chain", f"Chuỗi toàn vẹn ({got['count']} dòng)")
        log.write("info", "audit.check", ok=True, count=got["count"])
    else:
        alerts.raise_("audit_chain", "chain", f"Chuỗi nhật ký gãy ở dòng {got['broken_at']}", got["reason"])
    return {"chain": got}


@op
def ack_alert(alert_id: str, by: str, note: str = "") -> dict:
    """POST /api/system/alerts/ack: “Đã xem” on an alert, by a role it is for; audited."""
    from control import alerts

    return {"alert": alerts.ack(alert_id, by, note)}

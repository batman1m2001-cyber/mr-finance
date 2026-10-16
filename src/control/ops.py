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
    """The ``audit_check`` job: walk the audit chain and the write-once segments; broken raises an alert for
    Compliance and Admin, whole again resolves it (BRD-NFR-12). When both hold, the rows added since the last
    segment are written to a new one (BRD-RULE-DATA-10, control/worm.py)."""
    from control import alerts, db, log, worm
    from control.audit import verify

    with db.tx() as con:
        got = verify(con)
        kept = worm.verify(con)
        added = worm.write(con) if got["ok"] and kept["ok"] else None
    if got["ok"]:
        alerts.resolve("audit_chain", "chain", f"Chuỗi toàn vẹn ({got['count']} dòng)")
        log.write("info", "audit.check", ok=True, count=got["count"], segment=added)
    else:
        alerts.raise_("audit_chain", "chain", f"Chuỗi nhật ký gãy ở dòng {got['broken_at']}", got["reason"])
    if kept["ok"]:
        alerts.resolve("audit_chain", "worm", f"Các đoạn chỉ-ghi-một-lần khớp ({kept['rows']} dòng)")
    else:
        alerts.raise_("audit_chain", "worm", f"Đoạn nhật ký {kept['broken']} không khớp", kept["reason"])
    return {"chain": got, "worm": kept, "segment": added}


@op
def ack_alert(alert_id: str, by: str, note: str = "") -> dict:
    """POST /api/system/alerts/ack: “Đã xem” on an alert, by a role it is for; audited."""
    from control import alerts

    return {"alert": alerts.ack(alert_id, by, note)}

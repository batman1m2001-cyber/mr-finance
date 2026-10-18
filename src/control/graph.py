"""config_propose_flow / config_decide_flow (POST /api/config/propose, /api/config/decide; FR-701); audit_check_flow
(the hourly chain check), heartbeat_flow (the 20-second heartbeat; NFR-03) and alert_ack_flow (POST
/api/system/alerts/ack; NFR-12); job_run_flow (POST /api/jobs/run: Admin runs a job now)."""

from operonx import END, START, graph

from control.ops import ack_alert, check_chain, decide, heartbeat, propose, run_job


@graph
def config_propose_flow(kind, data, by, note=""):
    """Propose a new version of one kind of configuration."""
    done = propose(kind=kind, data=data, by=by, note=note)
    START >> done >> END


@graph
def config_decide_flow(version_id, action, by, note=""):
    """Approve or reject a proposed version."""
    done = decide(version_id=version_id, action=action, by=by, note=note)
    START >> done >> END


@graph
def audit_check_flow(tick=None, at=None):
    """The audit chain walked; an alert when it is broken."""
    done = check_chain(tick=tick, at=at)
    START >> done >> END


@graph
def heartbeat_flow(tick=None, at=None):
    """This minute recorded as up; the month's availability checked."""
    done = heartbeat(tick=tick, at=at)
    START >> done >> END


@graph
def alert_ack_flow(alert_id, by, note=""):
    """Someone who should look acknowledges an alert."""
    done = ack_alert(alert_id=alert_id, by=by, note=note)
    START >> done >> END


@graph
def job_run_flow(job, by):
    """Admin runs a background job now; it runs in the server's loop and records how it went."""
    done = run_job(job=job, by=by)
    START >> done >> END

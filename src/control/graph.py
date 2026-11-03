"""admin_flow: one flow for the Admin's and the CIO's small writes, a route picks its `task` (app/main.py binds it with
`variants`, and `bodies.py` is each route's request contract); the two jobs take theirs through `Job(inputs=...)`.

config_propose   POST /api/config/propose         propose a new version of one kind of configuration (FR-701)
config_decide    POST /api/config/decide          approve or reject a proposed version
alert_ack        POST /api/system/alerts/ack      someone who should look acknowledges an alert (NFR-12)
job_run          POST /api/jobs/run               Admin runs a background job now
account_request  POST /api/accounts/request       a request on a staff account, waiting for a second Admin (Q-25)
account_decide   POST /api/accounts/decide        approve, reject or withdraw a request on a staff account
model_estimate   POST /api/model/estimate         the estimated model proposed as the next factor_model version
market_load      POST /api/market/load            an Admin queues a load of the market history (Hệ thống)
audit_check      the hourly job                   the audit chain walked; an alert when it is broken
heartbeat        the 20-second job                this minute recorded as up; the month's availability checked (NFR-03)"""

from operonx import END, START, graph
from operonx.core.ops import if_

from control.ops import ack_alert, check_chain, decide, heartbeat, propose, run_job
from market.ops import ask_load, propose_estimate
from people.ops import decide_request, file_request


@graph
def admin_flow(
    task="config_propose",
    kind=None,
    data=None,
    by=None,
    note="",
    version_id=None,
    action=None,
    alert_id=None,
    job=None,
    request_id=None,
    person_id="",
    full_name="",
    email="",
    role="",
    title="",
    end=None,
    since="2020-01-01",
    tick=None,
    at=None,
):
    """One write per task, each the op its old flow ran: ``action`` is the request's own field (approve|reject...),
    ``task`` picks the route."""
    proposed = propose(kind=kind, data=data, by=by, note=note)
    decided = decide(version_id=version_id, action=action, by=by, note=note)
    acked = ack_alert(alert_id=alert_id, by=by, note=note)
    ran = run_job(job=job, by=by)
    filed = file_request(
        kind=kind, by=by, person_id=person_id, name=full_name, email=email, role=role, title=title, note=note
    )
    request_decided = decide_request(request_id=request_id, action=action, by=by, note=note)
    estimated = propose_estimate(by=by, end=end, note=note)
    asked = ask_load(by=by, since=since)
    chain = check_chain(tick=tick, at=at)
    beat = heartbeat(tick=tick, at=at)

    t = task
    START >> if_(t == "config_decide", decided).if_(t == "alert_ack", acked).if_(t == "job_run", ran).if_(
        t == "account_request", filed
    ).if_(t == "account_decide", request_decided).if_(t == "model_estimate", estimated).if_(
        t == "market_load", asked
    ).if_(t == "audit_check", chain).if_(t == "heartbeat", beat).else_(proposed)
    proposed >> END
    decided >> END
    acked >> END
    ran >> END
    filed >> END
    request_decided >> END
    estimated >> END
    asked >> END
    chain >> END
    beat >> END


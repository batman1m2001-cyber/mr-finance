"""Control: versioned configuration, accounts, alerts, model estimates, jobs run by hand, the audit and heartbeat.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from typing import Any

from operonx.app import Service, http
from operonx.app.jobs import Job

from app.serve import PORT, schedule
from control.graph import admin_flow


def config_propose(kind: str, data: Any, by: str, note: str = ""): ...


def config_decide(version_id: str, action: str, by: str, note: str = ""): ...


def alert_ack(alert_id: str, by: str, note: str = ""): ...


def job_run(job: str, by: str): ...


def account_request(
    kind: str,
    by: str,
    person_id: str = "",
    full_name: str = "",
    email: str = "",
    role: str = "",
    title: str = "",
    note: str = "",
): ...


def account_decide(request_id: str, action: str, by: str, note: str = ""): ...


def model_estimate(by: str, end: Any = None, note: str = ""): ...


def market_load(by: str, since: str = "2020-01-01"): ...


SERVICES = [
    Service(
        "config_propose",
        http("POST", "/api/config/propose", port=PORT),
        graph=admin_flow,
        variants={"config_propose": {"task": "config_propose"}},
        body=config_propose,
        description="POST {kind, data, by, note}: propose a configuration version (FR-701).",
    ),
    Service(
        "config_decide",
        http("POST", "/api/config/decide", port=PORT),
        graph=admin_flow,
        variants={"config_decide": {"task": "config_decide"}},
        body=config_decide,
        description="POST {version_id, action: approve|reject, by, note}: decide a proposed version.",
    ),
    Service(
        "model_estimate",
        http("POST", "/api/model/estimate", port=PORT),
        graph=admin_flow,
        variants={"model_estimate": {"task": "model_estimate"}},
        body=model_estimate,
        description="POST {by, end?, note?}: a CIO proposes the model estimated from market history (F2).",
    ),
    Service(
        "market_load_ask",
        http("POST", "/api/market/load", port=PORT),
        graph=admin_flow,
        variants={"market_load": {"task": "market_load"}},
        body=market_load,
        description="POST {by, since}: an Admin queues a load of the market history (the market_load job runs it).",
    ),
    Service(
        "alert_ack",
        http("POST", "/api/system/alerts/ack", port=PORT),
        graph=admin_flow,
        variants={"alert_ack": {"task": "alert_ack"}},
        body=alert_ack,
        description="POST {alert_id, by, note?}: “Đã xem” on an alert, by a role it is for (NFR-12).",
    ),
    Service(
        "account_request",
        http("POST", "/api/accounts/request", port=PORT),
        graph=admin_flow,
        variants={"account_request": {"task": "account_request"}},
        body=account_request,
        description="POST {kind: add|role|disable|enable|reset, by, person_id?, full_name?, email?, role?, title?, "
        "note?}: one Admin asks for a change to a staff account (Q-25); another Admin decides.",
    ),
    Service(
        "account_decide",
        http("POST", "/api/accounts/decide", port=PORT),
        graph=admin_flow,
        variants={"account_decide": {"task": "account_decide"}},
        body=account_decide,
        description="POST {request_id, action: approve|reject|withdraw, by, note?}: a second Admin approves or "
        "rejects (a reason), the proposer withdraws; an approved add or reset answers a one-time code once.",
    ),
    Service(
        "job_run",
        http("POST", "/api/jobs/run", port=PORT),
        graph=admin_flow,
        variants={"job_run": {"task": "job_run"}},
        body=job_run,
        description="POST {job, by}: Admin runs a background job now (control/jobs.py RUNNABLE); one at a time.",
    ),
]


JOBS = [
    Job(
        "audit_check",
        graph=admin_flow,
        inputs={"task": "audit_check"},
        schedule=schedule(every="1h", port=PORT),
        timeout=600,
        description="Hourly: the audit chain walked and new rows copied to write-once segments; an alert for "
        "the CIO and Admin when either is broken.",
    ),
    Job(
        "heartbeat",
        graph=admin_flow,
        inputs={"task": "heartbeat"},
        schedule=schedule(every="20s", port=PORT),
        timeout=30,
        keep_runs=200,
        description="Every 20 seconds: this minute recorded as up; availability in business hours against "
        "99.5 %, an alert for Admin below it (NFR-03).",
    ),
]

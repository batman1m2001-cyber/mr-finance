"""Each admin route's request contract (Service(body=...), app/main.py): the fields it accepts, which are required,
and their defaults. The functions are never called; control/graph.py admin_flow serves every route."""

from typing import Any


def config_propose(kind: str, data: Any, by: str, note: str = ""):
    ...


def config_decide(version_id: str, action: str, by: str, note: str = ""):
    ...


def alert_ack(alert_id: str, by: str, note: str = ""):
    ...


def job_run(job: str, by: str):
    ...


def account_request(
    kind: str, by: str, person_id: str = "", full_name: str = "", email: str = "", role: str = "", title: str = "", note: str = ""
):
    ...


def account_decide(request_id: str, action: str, by: str, note: str = ""):
    ...


def model_estimate(by: str, end: Any = None, note: str = ""):
    ...


def market_load(by: str, since: str = "2020-01-01"):
    ...

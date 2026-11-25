"""Review: the RM queue, decisions, recommendations, house views and application runs.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from typing import Any, Optional

from operonx.app import Service, http

from app.serve import PORT
from review.graph import review_flow


def propose(
    client_id: str,
    option: Any,
    scenario: Optional[str] = None,
    title: Optional[str] = None,
    summary: Optional[str] = None,
): ...


def decide(item_id: str, decision: str, note: Optional[str] = None, by: Optional[str] = None): ...


def recommend(client_id: str, title: str, actions: Any, note: Optional[str] = None, by: Optional[str] = None): ...


def view(
    view_id: str,
    action: str,
    by: str,
    reason: str = "",
    idem_key: Optional[str] = None,
    edits: Any = None,
    responses: Any = None,
): ...


def recompute(run: str, by: str = "cio", idem_key: Optional[str] = None): ...


def run(run: str, action: str, by: str, reason: str = ""): ...


SERVICES = [
    Service(
        "propose",
        http("POST", "/api/review/propose", port=PORT),
        graph=review_flow,
        variants={"propose": {"task": "propose"}},
        body=propose,
        description="POST {client_id, scenario, title, option}: an option sent to the RM queue.",
    ),
    Service(
        "decide",
        http("POST", "/api/review/decide", port=PORT),
        graph=review_flow,
        variants={"decide": {"task": "decide"}},
        body=decide,
        description="POST {item_id, decision: approved|rejected, note?}: the RM's decision.",
    ),
    Service(
        "recommend",
        http("POST", "/api/review/recommend", port=PORT),
        graph=review_flow,
        variants={"recommend": {"task": "recommend"}},
        body=recommend,
        description="POST {client_id, title, actions, note?, by}: the RM writes an action recommendation for a "
        "family; it reaches the client at once (the RM's alone, OWN-FB-18).",
    ),
    Service(
        "view_decide",
        http("POST", "/api/views/decide", port=PORT),
        graph=review_flow,
        variants={"view": {"task": "view"}},
        body=view,
        description="POST {view_id, action, by, reason, idem_key?, edits?, responses?}: one CIO action.",
    ),
    Service(
        "run_recompute",
        http("POST", "/api/runs/recompute", port=PORT),
        graph=review_flow,
        variants={"recompute": {"task": "recompute"}},
        body=recompute,
        description="POST {run_id, by, idem_key?}: re-apply the run's view on today's data and compare.",
    ),
    Service(
        "run_decide",
        http("POST", "/api/runs/decide", port=PORT),
        graph=review_flow,
        variants={"run": {"task": "run"}},
        body=run,
        description="POST {run_id, action: make_effective|withdraw, by, reason}: the CIO on a run.",
    ),
]

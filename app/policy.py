"""Policy (FR-306): a document added, verified, its status, summarised.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from operonx.app import Service, http

from app.serve import PORT
from policy.graph import policy_flow


def add(item, by): ...


def verify(document_id, by, note=""): ...


def status(document_id, status, by, note="", date=None): ...


def summarise(document_id, by, mode=""): ...


SERVICES = [
    Service(
        "policy_add",
        http("POST", "/api/policy", port=PORT),
        graph=policy_flow,
        variants={"add": {"action": "add"}},
        body=add,
        description="POST {item: {gazette_url} | {source_url, title, number?, issued?, text?, status}, by}.",
    ),
    Service(
        "policy_verify",
        http("POST", "/api/policy/verify", port=PORT),
        graph=policy_flow,
        variants={"verify": {"action": "verify"}},
        body=verify,
        description="POST {document_id, by, note}: a second CIO confirms the source (FR-306).",
    ),
    Service(
        "policy_status",
        http("POST", "/api/policy/status", port=PORT),
        graph=policy_flow,
        variants={"status": {"action": "status"}},
        body=status,
        description="POST {document_id, status, by, note, date?}: where the document stands (the radar).",
    ),
    Service(
        "policy_summarise",
        http("POST", "/api/policy/summarise", port=PORT),
        graph=policy_flow,
        variants={"summarise": {"action": "summarise"}},
        body=summarise,
        description="POST {document_id, by, mode?}: the policy agent on a verified document (FR-306).",
    ),
]

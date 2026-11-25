"""Evidence (NEWS_EVIDENCE_BRD): each item's evidence, the CIO's decisions, drafts and event types.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from operonx.app import Service, http

from app.serve import PORT
from evidence.graph import evidence_flow


def read(factor=None, role=None): ...


def decide(factor=None, decision=None, by=None, note=""): ...


def draft(news_id=None, by=None, mode=""): ...


def draft_decide(news_id=None, decision=None, by=None, note=""): ...


def type(event_type=None, label=None, dates=None, series=None, by=None): ...


SERVICES = [
    Service(
        "evidence",
        http("POST", "/api/evidence", port=PORT),
        graph=evidence_flow,
        variants={"read": {"action": "read"}},
        body=read,
        description="POST {factor?, role?}: each news item's evidence (statistics or qualitative frame).",
    ),
    Service(
        "evidence_decide",
        http("POST", "/api/evidence/decide", port=PORT),
        graph=evidence_flow,
        variants={"decide": {"action": "decide"}},
        body=decide,
        description="POST {factor, decision, by, note?}: the CIO approves, returns or rejects a frame.",
    ),
    Service(
        "evidence_draft",
        http("POST", "/api/evidence/draft", port=PORT),
        graph=evidence_flow,
        variants={"draft": {"action": "draft"}},
        body=draft,
        description="POST {news_id, by, mode?}: the evidence agent drafts one news item's frame for the CIO.",
    ),
    Service(
        "evidence_draft_decide",
        http("POST", "/api/evidence/draft/decide", port=PORT),
        graph=evidence_flow,
        variants={"draft_decide": {"action": "draft_decide"}},
        body=draft_decide,
        description="POST {news_id, decision, by, note?}: the CIO approves, returns or rejects the agent's draft.",
    ),
    Service(
        "evidence_type",
        http("POST", "/api/evidence/type", port=PORT),
        graph=evidence_flow,
        variants={"type": {"action": "type"}},
        body=type,
        description="POST {event_type? | label?, dates, series?, by}: the CIO adds an event type or its precedent dates.",
    ),
]

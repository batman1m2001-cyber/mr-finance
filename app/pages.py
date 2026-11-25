"""The pages' routes: dashboard, overview, timeline, Money Flow, the feed, search, the risk test, an RM's contact.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from typing import Any, Optional

from operonx.app import Service, http

from app.serve import PORT
from pages.graph import pages_flow


def dashboard(client_id: str, scope: str = "personal", months: int = 12): ...


def overview(client_id: str, scope: str = "personal", role: str = "client", goals: Optional[Any] = None): ...


def timeline(client_id: str, scope: str = "personal", node: str = "ME", unit: str = "month"): ...


def flows(client_id: str, scope: str = "personal", month: Optional[str] = None): ...


def feed(client_id: str, scope: str = "personal", role: str = "client"): ...


def feed_open(client_id: str, key: str): ...


def search(q: str, role: str, client_id: Optional[str] = None, scope: str = "personal"): ...


def risk(client_id: str, answers: Optional[Any] = None): ...


def contact(
    family_id: str,
    channel: str = "call",
    signal: Optional[str] = None,
    note: Optional[str] = None,
    by: Optional[str] = None,
): ...


SERVICES = [
    Service(
        "dashboard",
        http("POST", "/api/dashboard", port=PORT),
        graph=pages_flow,
        variants={"dashboard": {"action": "dashboard"}},
        body=dashboard,
        description="POST {client_id, scope: personal|family, months}: the dashboard.",
    ),
    Service(
        "overview",
        http("POST", "/api/overview", port=PORT),
        graph=pages_flow,
        variants={"overview": {"action": "overview"}},
        body=overview,
        description="POST {client_id, scope, role: client|rm, goals}: the overview graph around one client.",
    ),
    Service(
        "timeline",
        http("POST", "/api/timeline", port=PORT),
        graph=pages_flow,
        variants={"timeline": {"action": "timeline"}},
        body=timeline,
        description="POST {client_id, scope, node, unit: day|month|year}: a node's money over time (simulated).",
    ),
    Service(
        "flows",
        http("POST", "/api/flows", port=PORT),
        graph=pages_flow,
        variants={"flows": {"action": "flows"}},
        body=flows,
        description="POST {client_id, scope: personal|family, month: YYYY-MM}: Money Flow from the transactions.",
    ),
    Service(
        "feed",
        http("POST", "/api/feed", port=PORT),
        graph=pages_flow,
        variants={"feed": {"action": "feed"}},
        body=feed,
        description="POST {client_id, scope, role: client|rm}: the Intelligence Feed, with why and evidence.",
    ),
    Service(
        "feed_open",
        http("POST", "/api/feed/open", port=PORT),
        graph=pages_flow,
        variants={"feed_open": {"action": "feed_open"}},
        body=feed_open,
        description="POST {client_id, key}: the client opened a high-level item (KPI-07).",
    ),
    Service(
        "rm_contact",
        http("POST", "/api/rm/contacts", port=PORT),
        graph=pages_flow,
        variants={"contact": {"action": "contact"}},
        body=contact,
        description="POST {family_id, channel, signal?, note?, by}: an RM records a contact, from a Hôm nay "
        "signal or not (KPI-06).",
    ),
    Service(
        "search",
        http("POST", "/api/search", port=PORT),
        graph=pages_flow,
        variants={"search": {"action": "search"}},
        body=search,
        description="POST {q, role, client_id?, scope?}: the header search over what the role may open.",
    ),
    Service(
        "risk",
        http("POST", "/api/risk", port=PORT),
        graph=pages_flow,
        variants={"risk": {"action": "risk"}},
        body=risk,
        description="POST {client_id, answers}: the next question of the risk test, or its result.",
    ),
]

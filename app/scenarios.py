"""Scenarios: one, several combined, and the life goals.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from typing import Any, Dict, List, Optional

from operonx.app import Service, http

from app.serve import PORT
from scenarios.graph import scenarios_flow


def scenario(client_id: str, scenario: str, params: Optional[Dict[str, Any]] = None, scope: str = "personal"): ...


def combine(
    client_id: str,
    scenarios: List[str],
    params: Optional[Dict[str, Any]] = None,
    scope: str = "personal",
    goals: Optional[List[str]] = None,
): ...


def goals(client_id: str, scope: str = "personal"): ...


SERVICES = [
    Service(
        "scenario",
        http("POST", "/api/scenario", port=PORT),
        graph=scenarios_flow,
        variants={"scenario": {"action": "scenario"}},
        body=scenario,
        description="POST {client_id, scenario, params?, scope?}: a life event or a stress test, with two options.",
    ),
    Service(
        "scenario_combine",
        http("POST", "/api/scenario/combine", port=PORT),
        graph=scenarios_flow,
        variants={"combine": {"action": "combine"}},
        body=combine,
        description="POST {client_id, scenarios, params?, scope?, goals?}: stress tests together, no double count.",
    ),
    Service(
        "goals",
        http("POST", "/api/goals", port=PORT),
        graph=scenarios_flow,
        variants={"goals": {"action": "goals"}},
        body=goals,
        description="POST {client_id, scope?}: every life goal, with its gap, status and actions.",
    ),
]

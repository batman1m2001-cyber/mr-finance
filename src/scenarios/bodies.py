"""Each planning route's request contract (Service(body=...), app/main.py): the fields it accepts, which are
required, and their defaults. The functions are never called; scenarios_flow's graph.py serves every route."""

from typing import Any, Dict, List, Optional


def scenario(client_id: str, scenario: str, params: Optional[Dict[str, Any]] = None, scope: str = "personal"):
    ...


def combine(
    client_id: str,
    scenarios: List[str],
    params: Optional[Dict[str, Any]] = None,
    scope: str = "personal",
    goals: Optional[List[str]] = None,
):
    ...


def goals(client_id: str, scope: str = "personal"):
    ...

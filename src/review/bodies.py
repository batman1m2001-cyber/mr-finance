"""Each review route's request contract (Service(body=...), app/main.py): the fields it accepts, which are required,
and their defaults. The functions are never called; review_flow's graph.py serves every route."""

from typing import Any, Optional


def propose(client_id: str, option: Any, scenario: Optional[str] = None, title: Optional[str] = None, summary: Optional[str] = None):
    ...


def decide(item_id: str, decision: str, note: Optional[str] = None, by: Optional[str] = None):
    ...


def recommend(client_id: str, title: str, actions: Any, note: Optional[str] = None, by: Optional[str] = None):
    ...

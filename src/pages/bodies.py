"""Each page route's request contract (Service(body=...), app/main.py): the fields it accepts, which are required,
and their defaults. The functions are never called; pages_flow's graph.py serves every route."""

from typing import Any, Optional


def dashboard(client_id: str, scope: str = "personal", months: int = 12):
    ...


def overview(client_id: str, scope: str = "personal", role: str = "client", goals: Optional[Any] = None):
    ...


def timeline(client_id: str, scope: str = "personal", node: str = "ME", unit: str = "month"):
    ...


def flows(client_id: str, scope: str = "personal", month: Optional[str] = None):
    ...


def feed(client_id: str, scope: str = "personal", role: str = "client"):
    ...


def feed_open(client_id: str, key: str):
    ...


def search(q: str, role: str, client_id: Optional[str] = None, scope: str = "personal"):
    ...


def risk(client_id: str, answers: Optional[Any] = None):
    ...


def contact(family_id: str, channel: str = "call", signal: Optional[str] = None, note: Optional[str] = None, by: Optional[str] = None):
    ...

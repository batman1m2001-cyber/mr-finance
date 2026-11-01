"""Each news, events and alerts route's request contract (Service(body=...), app/main.py): the fields it accepts, which
are required, and their defaults. The functions are never called; news_flow's graph.py serves every route."""

from typing import Any, Dict, List, Optional


def ingest(feeds: Optional[Dict[str, Any]] = None, now: Any = None, tick: Any = None, at: Any = None):
    ...


def dismiss(ids: List[str], by: str = "cio", note: str = ""):
    ...


def release(item_id: str, by: str, note: str):
    ...


def event(news_ids: List[str], title: Optional[str] = None, by: str = "cio"):
    ...


def urgent(event_id: str, urgent: bool = True, reason: str = "", by: str = "cio"):
    ...


def queue(event_id: str, by: str = "cio", mode: Optional[str] = None):
    ...


def alerts(client_id: str, scope: str = "personal"):
    ...

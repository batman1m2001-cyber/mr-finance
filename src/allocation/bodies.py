"""Each allocation route's request contract (Service(body=...), app/main.py): the fields it accepts, which are
required, and their defaults. The functions are never called; allocation_flow's graph.py serves every route."""

from typing import Any, Dict, Optional


def view(client_id: str, scope: str = "family", method: str = "A", assumptions: Optional[Dict[str, Any]] = None, role: Optional[str] = None, whatif: Optional[Dict[str, Any]] = None):
    ...


def example(method: str = "A", assumptions: Optional[Dict[str, Any]] = None, role: Optional[str] = None):
    ...


def tilt(asset_class: str, stance: str, view_id: str, by: str, reason: str = ""):
    ...


def tilts():
    ...


def send(client_id: str, by: str, scope: str = "family", method: str = "A", assumptions: Optional[Dict[str, Any]] = None):
    ...


def review(item_id: str, by: str, decisions: Optional[Dict[str, Any]] = None, note: str = ""):
    ...


def queue():
    ...


def override(client_id: str, key: str, by: str, bucket: str = "", reason: str = "", scope: str = "family"):
    ...


def method(method: str, by: str):
    ...

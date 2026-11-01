"""Each client-data route's request contract (Service(body=...), app/main.py): the fields it accepts, which are
required, and their defaults. The functions are never called; statements/graph.py intake_flow serves both routes."""

from typing import Optional


def statement(client_id: str, filename: str, content: str):
    ...


def declare(client_id: str, message: str, session_id: Optional[str] = None):
    ...

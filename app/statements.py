"""Statements and declarations: a statement read, a chat turn of declarations (also streamed), the reading eval.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from typing import Optional

from operonx.app import Eval, Service, http
from operonx.app.evals import Gate

from app.serve import PORT
from declare.graph import declare_stream_flow
from statements.checks import items_match
from statements.graph import intake_flow


def statement(client_id: str, filename: str, content: str): ...


def declare(client_id: str, message: str, session_id: Optional[str] = None): ...


SERVICES = [
    Service(
        "statement",
        http("POST", "/api/statement", port=PORT),
        graph=intake_flow,
        variants={"statement": {"action": "statement"}},
        body=statement,
        description="POST {client_id, filename, content: base64}: a statement, read and kept.",
    ),
    Service(
        "declare",
        http("POST", "/api/declare", port=PORT),
        graph=intake_flow,
        variants={"declare": {"action": "declare"}},
        body=declare,
        description="POST {client_id, message, session_id}: one chat turn of declarations.",
    ),
    Service(
        "declare_stream",
        http("POST", "/api/declare/stream", port=PORT),
        graph=declare_stream_flow,
        description="POST the same body as /api/declare, Accept: text/event-stream: the turn as it happens — "
        "step, text, form (what the agent asks back), then the answer.",
    ),
]


JOBS = [
    # how well statements are read: `operonx run statement_reading` (exit code: the gate's).
    # The three demo samples must pass; the free-text note needs a model (MF_AI=on).
    Eval(
        "statement_reading",
        graph=intake_flow,
        inputs={"action": "sample"},
        input="filename",
        dataset="dataset:statements",
        evaluators=[items_match],
        gate=Gate(threshold=0.8),
    ),
]

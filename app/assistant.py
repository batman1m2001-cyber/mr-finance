"""The assistant: Copilot, turns (also streamed and by voice), conversations, memory, attachments, and its jobs.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from operonx.app import Service, http, websocket
from operonx.app.jobs import Job

from app.serve import PORT, schedule
from assistant.graph import assistant_flow, assistant_stream_flow
from voice.graph import assistant_voice_flow


def turn(message=None, role="client", client_id=None, scope="personal", route=None, goals=None, turn_id=None,
         approvals=None, conversation_id=None, graph=None, attachments=None):  # fmt: skip
    ...


def copilot(question=None, role="client", client_id=None, scope="personal", route=None, confirm=None, goals=None): ...


def conversations(action="list", conversation_id=None, role="client", client_id=None, title=None): ...


def memory(action="list", item_id=None, text=None, kind=None, query=None, role="client", client_id=None,
           file_name=None, data=None, key=None):  # fmt: skip
    ...


def attach(role="client", client_id=None, file_name=None, data=None): ...


SERVICES = [
    Service(
        "copilot",
        http("POST", "/api/copilot", port=PORT),
        graph=assistant_flow,
        variants={"copilot": {"task": "copilot"}},
        body=copilot,
        description="POST {question, role, client_id, scope, route, confirm}: the Copilot (routes, never reads).",
    ),
    Service(
        "assistant",
        http("POST", "/api/assistant", port=PORT),
        graph=assistant_flow,
        variants={"turn": {"task": "turn"}},
        body=turn,
        description="POST {message | turn_id + approvals, role, client_id, scope, route, goals, conversation_id}: "
        "the assistant (A2) — the role's tools in several steps, writes confirmed and verified, kept in a "
        "conversation (A3); the Copilot's path when no model answers.",
    ),
    Service(
        "assistant_stream",
        http("POST", "/api/assistant/stream", port=PORT),
        graph=assistant_stream_flow,
        description="POST the same body as /api/assistant, Accept: text/event-stream: the turn as it happens — "
        "step (a tool starting and ending, with the graph nodes it reads), text, wait, then the answer (FEAT-40).",
    ),
    Service(
        "assistant_conversations",
        http("POST", "/api/assistant/conversations", port=PORT),
        graph=assistant_flow,
        variants={"conversations": {"task": "conversations"}},
        body=conversations,
        description="POST {action: list | open | delete, conversation_id, role, client_id}: the person's "
        "conversations with the assistant (A3).",
    ),
    Service(
        "assistant_memory",
        http("POST", "/api/assistant/memory", port=PORT),
        graph=assistant_flow,
        variants={"memory": {"task": "memory"}},
        body=memory,
        description="POST {action: list | search | update | delete | clear, item_id, text, kind, query, role, "
        "client_id}: the Bộ nhớ page (A4).",
    ),
    Service(
        "assistant_attach",
        http("POST", "/api/assistant/attach", port=PORT),
        graph=assistant_flow,
        variants={"attach": {"task": "attach"}},
        body=attach,
        description="POST {file_name, data: base64, role, client_id}: a file or image for the assistant, read "
        "once and kept 24 hours (docs/OCR_PLAN.md).",
    ),
    Service(
        "assistant_voice",
        websocket("/api/assistant/voice", port=PORT),
        graph=assistant_voice_flow,
        max_inflight=4000,
        description="WS ?rate=&silence_ms=: microphone PCM (int16) in; heard, asked, and the answer's sentences "
        "as WAVs out, from the panel's say frames (the callbot's VAD, STT, TTS).",
    ),
]


JOBS = [
    # the assistant's retention (A4): conversations past the CIO's assistant_retention, expired memory items
    Job(
        "assistant_retention",
        graph=assistant_flow,
        inputs={"task": "retention"},
        schedule=schedule(at="02:30", port=PORT),
        description="02:30 daily: the assistant's conversations past retention and expired memory items deleted.",
    ),
    # the memory consolidator (A6, ADR-0031): idle conversations into long-term items, ≤ 8,000 tokens each
    Job(
        "assistant_consolidate",
        graph=assistant_flow,
        inputs={"task": "consolidate"},
        schedule=schedule(every="5m", port=PORT),
        timeout=600,
        description="Every 5 minutes: conversations idle 15 minutes distilled into the person's memory (A6).",
    ),
]

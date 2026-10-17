"""assistant_flow: a message (or the person's answers to the writes it waits on) → one assistant turn → the answer
(POST /api/assistant, A2), kept in its conversation (A3). assistant_conversations_flow: the person's sessions — list,
open, rename, archive, restore, describe, delete (POST /api/assistant/conversations). The Copilot's ``copilot_flow``
stays as the fallback path and its own endpoint. assistant_stream_flow: the same turn said as it happens
(POST /api/assistant/stream with ``Accept: text/event-stream``, FEAT-40): one numbered server-sent event per step,
text, wait and the answer."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress

from assistant.ops import (
    answer,
    check_request,
    consolidate_due,
    conversations,
    memory_page,
    retention_sweep,
    stream_turn,
    turn,
)


@graph
def assistant_flow(
    message=None,
    role="client",
    client_id=None,
    scope="personal",
    route=None,
    goals=None,
    turn_id=None,
    approvals=None,
    conversation_id=None,
):
    """Ask OneWealth: the role's tools in as many steps as the question needs; writes wait for the person."""
    ask = check_request(
        message=message,
        role=role,
        client_id=client_id,
        scope=scope,
        route=route,
        goals=goals,
        turn_id=turn_id,
        approvals=approvals,
        conversation_id=conversation_id,
    )
    done = turn(request=ask["request"])
    out = answer(request=ask["request"], result=done["result"])
    START >> ask >> done >> out >> END


@graph
def assistant_stream_flow():
    """The body is the one request (as POST /api/assistant takes it); every event of the turn goes back at once."""
    src = ingress()
    ev = stream_turn(item=src["item"])
    out = egress(item=ev["event"])
    START >> src >> ev >> out >> END


@graph
def assistant_conversations_flow(action="list", conversation_id=None, role="client", client_id=None, title=None):
    """The person's sessions with the assistant: list (active or archived), open, rename, archive, restore, delete."""
    got = conversations(action=action, conversation_id=conversation_id, role=role, client_id=client_id, title=title)
    START >> got >> END


@graph
def assistant_memory_flow(action="list", item_id=None, text=None, kind=None, query=None, role="client", client_id=None,
                          file_name=None, data=None, key=None):  # fmt: skip
    """The Bộ nhớ page: what the assistant remembers about the person, their past conversations' search, and the
    documents they added (A5)."""
    got = memory_page(action=action, item_id=item_id, text=text, kind=kind, query=query, role=role, client_id=client_id,
                      file_name=file_name, data=data, key=key)  # fmt: skip
    START >> got >> END


@graph
def assistant_retention_flow():
    """Daily: conversations past Compliance's retention, and expired memory items, deleted."""
    swept = retention_sweep()
    START >> swept >> END


@graph
def assistant_consolidate_flow(tick=None, at=None):
    """Every 5 minutes: idle conversations distilled into long-term memory (A6)."""
    done = consolidate_due(tick=tick, at=at)
    START >> done >> END

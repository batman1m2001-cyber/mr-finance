"""assistant_flow: a message (or the person's answers to the writes it waits on) → one assistant turn → the answer
(POST /api/assistant, A2), kept in its conversation (A3). assistant_conversations_flow: the person's conversations —
list, open, delete (POST /api/assistant/conversations). The Copilot's ``copilot_flow`` stays as the fallback path
and its own endpoint."""

from operonx import END, START, graph

from assistant.ops import answer, check_request, conversations, memory_page, retention_sweep, turn


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
def assistant_conversations_flow(action="list", conversation_id=None, role="client", client_id=None):
    """The person's conversations with the assistant: list, open one, delete one."""
    got = conversations(action=action, conversation_id=conversation_id, role=role, client_id=client_id)
    START >> got >> END


@graph
def assistant_memory_flow(action="list", item_id=None, text=None, kind=None, query=None, role="client", client_id=None):
    """The Bộ nhớ page: what the assistant remembers about the person, and their past conversations' search."""
    got = memory_page(action=action, item_id=item_id, text=text, kind=kind, query=query, role=role, client_id=client_id)
    START >> got >> END


@graph
def assistant_retention_flow():
    """Daily: conversations past Compliance's retention, and expired memory items, deleted."""
    swept = retention_sweep()
    START >> swept >> END

"""assistant_flow: a message (or the person's answers to the writes it waits on) → one assistant turn → the answer
(POST /api/assistant, A2). The Copilot's ``copilot_flow`` stays as the fallback path and its own endpoint."""

from operonx import END, START, graph

from assistant.ops import answer, check_request, turn


@graph
def assistant_flow(
    message=None, role="client", client_id=None, scope="personal", route=None, goals=None, turn_id=None, approvals=None
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
    )
    done = turn(request=ask["request"])
    out = answer(request=ask["request"], result=done["result"])
    START >> ask >> done >> out >> END

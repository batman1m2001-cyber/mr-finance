"""assistant_flow: one flow for the assistant's request–reply routes and its two jobs; a route picks its `task`
(app/main.py binds it with `variants`, a job with `Job(inputs=...)`, and `bodies.py` is each route's request
contract). The selector is not called `action`: the conversations and memory bodies have a field of that name.

turn           POST /api/assistant                a message (or the person's answers to the writes it waits on) →
               one assistant turn → the answer, kept in its conversation (A2, A3)
copilot        POST /api/copilot                  a question and the page → one tool call → a templated answer; the
               fallback path when no model answers (NFR-03)
conversations  POST /api/assistant/conversations  the person's sessions — list, open, rename, archive, restore, delete
memory         POST /api/assistant/memory         the Bộ nhớ page: what the assistant remembers, search, documents (A4, A5)
attach         POST /api/assistant/attach         a file or image attached in the panel, read once, kept 24 hours
retention      assistant_retention job, 02:30     conversations past the CIO's retention and expired memory deleted
consolidate    assistant_consolidate job, 5 min   idle conversations distilled into long-term memory (A6)

assistant_stream_flow: the same turn said as it happens (POST /api/assistant/stream with ``Accept: text/event-stream``,
FEAT-40): one numbered server-sent event per step, text, wait and the answer. It has doors, so it stays its own flow.
The AgentOp-with-memory move (docs/FEATURE_FLOWS_PLAN.md D3) is not done here: the turn runs as before."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress
from operonx.core.ops import if_

from assistant.ops import (
    answer,
    attach,
    check_request,
    consolidate_due,
    conversations,
    memory_page,
    retention_sweep,
    stream_turn,
    turn,
)
from copilot.ops import act as copilot_act
from copilot.ops import answer as copilot_answer
from copilot.ops import check_request as copilot_check
from copilot.ops import decide as copilot_decide


@graph
def assistant_flow(
    task="turn",
    message=None,
    role="client",
    client_id=None,
    scope="personal",
    route=None,
    goals=None,
    turn_id=None,
    approvals=None,
    conversation_id=None,
    graph=None,
    attachments=None,
    question=None,
    confirm=None,
    action="list",
    title=None,
    item_id=None,
    text=None,
    kind=None,
    query=None,
    file_name=None,
    data=None,
    key=None,
    tick=None,
    at=None,
):
    """Ask OneWealth: the role's tools in as many steps as the question needs; writes wait for the person. The other
    tasks are the Copilot, the person's conversations and memory, an attachment, and the two daily jobs."""
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
        graph=graph,
        attachments=attachments,
    )
    done = turn(request=ask["request"])
    out = answer(request=ask["request"], result=done["result"])
    copilot_ask = copilot_check(
        question=question, role=role, client_id=client_id, scope=scope, route=route, confirm=confirm, goals=goals
    )
    pick = copilot_decide(
        question=copilot_ask["question"], role=copilot_ask["role"], route=copilot_ask["route"], confirm=copilot_ask["confirm"]
    )
    tool = copilot_act(
        tool=pick["tool"],
        args=pick["args"],
        confirmed=pick["confirmed"],
        role=copilot_ask["role"],
        client_id=copilot_ask["client_id"],
        scope=copilot_ask["scope"],
        question=copilot_ask["question"],
        followed=copilot_ask["followed"],
    )
    reply = copilot_answer(
        result=tool["result"],
        seen=pick["seen"],
        router_info=pick["router"],
        role=copilot_ask["role"],
        client_id=copilot_ask["client_id"],
    )
    sessions = conversations(action=action, conversation_id=conversation_id, role=role, client_id=client_id, title=title)
    remembered = memory_page(action=action, item_id=item_id, text=text, kind=kind, query=query, role=role, client_id=client_id,
                             file_name=file_name, data=data, key=key)  # fmt: skip
    attached = attach(role=role, client_id=client_id, file_name=file_name, data=data)
    swept = retention_sweep()
    distilled = consolidate_due(tick=tick, at=at)

    t = task
    START >> if_(t == "copilot", copilot_ask).if_(t == "conversations", sessions).if_(t == "memory", remembered).if_(
        t == "attach", attached
    ).if_(t == "retention", swept).if_(t == "consolidate", distilled).else_(ask)
    ask >> done >> out >> END
    copilot_ask >> pick >> tool >> reply >> END
    sessions >> END
    remembered >> END
    attached >> END
    swept >> END
    distilled >> END


@graph
def assistant_stream_flow():
    """The body is the one request (as POST /api/assistant takes it); every event of the turn goes back at once."""
    src = ingress()
    ev = stream_turn(item=src["item"])
    out = egress(item=ev["event"])
    START >> src >> ev >> out >> END

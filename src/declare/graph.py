"""declare_flow: one chat turn — the agent records what the client says (when AI is on), or the
rules do — and what the turn added to their profile. declare_stream_flow: the same turn said as it happens
(POST /api/declare/stream, Accept: text/event-stream)."""

from operonx import END, START, graph
from operonx.agents import AgentOp
from operonx.app.serve import egress, ingress
from operonx.core.ops import if_

from declare.agent import DECLARER, DECLARER_ONPREM
from declare.ops import agent_answer, ai_mode, chat_session, check_request, recorded, rule_declare, stream_declare


@graph
def declare_flow(client_id, message, session_id=None):
    """One message from the client (POST /api/declare), recorded as their tier-3 declarations."""
    ask = check_request(client_id=client_id, message=message, session_id=session_id)
    client_id, message, session_id = ask["client_id"], ask["message"], ask["session_id"]
    mode = ai_mode()
    agent = AgentOp.of(agent=DECLARER, input=message, session_id=session_id, deps=client_id, sessions=chat_session)
    onprem = AgentOp.of(
        agent=DECLARER_ONPREM, input=message, session_id=session_id, deps=client_id, sessions=chat_session
    )
    said = agent_answer(
        client_id=client_id,
        message=message,
        output=agent["output"],
        status=agent["status"],
        error=agent["error"],
        onprem_output=onprem["output"],
        onprem_status=onprem["status"],
        onprem_error=onprem["error"],
    )
    rules = rule_declare(client_id=client_id, message=message)
    turn = recorded(
        client_id=client_id,
        since=mode["since"],
        ai_reply=said["reply"],
        rule_reply=rules["reply"],
        ai_method=said["method"],
        rule_method=rules["method"],
    )
    START >> ask >> mode >> if_(mode["assistant"] == True, agent).if_(mode["onprem"] == True, onprem).else_(rules)  # noqa: E712
    agent >> said
    onprem >> said
    said >> turn
    rules >> turn
    turn >> END


@graph
def declare_stream_flow():
    """The body is the one request (as POST /api/declare takes it); every event of the turn goes back at once."""
    src = ingress()
    ev = stream_declare(item=src["item"])
    out = egress(item=ev["event"])
    START >> src >> ev >> out >> END

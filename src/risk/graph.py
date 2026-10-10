"""risk_flow: the client's data → the next question, or (all answered) the result."""

from operonx import END, START, graph
from operonx.core.ops import if_

from consolidate.graph import consolidate_flow
from risk.ops import ask, check_request, context, next_step, reply, result


@graph
def risk_flow(client_id, answers=None):
    """One step of the adaptive risk test (POST /api/risk): the next question, or the result."""
    checked = check_request(client_id=client_id, answers=answers)
    client_id, answers = checked["client_id"], checked["answers"]
    held = consolidate_flow(client_id=client_id, scope="personal")
    data = context(client_id=client_id, holdings=held["holdings"], transactions=held["transactions"])
    step = next_step(answers=answers, ctx=data["ctx"])
    asked = ask(qid=step["qid"], answers=answers, ctx=data["ctx"])
    done = result(client_id=client_id, answers=answers, ctx=data["ctx"])
    out = reply(asked=asked["reply"], done=done["reply"])
    START >> checked >> held >> data >> step >> if_(step["done"] == True, done).else_(asked)  # noqa: E712
    asked >> out
    done >> out
    out >> END

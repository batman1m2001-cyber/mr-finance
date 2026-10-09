"""risk_flow: the client's data → the next question, or (all answered) the result."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress
from operonx.core.ops import if_

from consolidate.graph import consolidate_flow
from risk.ops import ask, context, next_step, read_request, reply, result


@graph
def risk_flow(client_id, answers):
    """One step of the adaptive risk test."""
    held = consolidate_flow(client_id=client_id, scope="personal")
    data = context(client_id=client_id, holdings=held["holdings"], transactions=held["transactions"])
    step = next_step(answers=answers, ctx=data["ctx"])
    asked = ask(qid=step["qid"], answers=answers, ctx=data["ctx"])
    done = result(client_id=client_id, answers=answers, ctx=data["ctx"])
    out = reply(asked=asked["reply"], done=done["reply"])
    START >> held >> data >> step >> if_(step["done"] == True, done).else_(asked)  # noqa: E712
    asked >> out
    done >> out
    out >> END


@graph
def risk_api():
    """POST {client_id, answers} → {question} or {result}."""
    req = ingress()
    ask_ = read_request(item=req["item"])
    test = risk_flow(client_id=ask_["client_id"], answers=ask_["answers"])
    out = egress(item=test["reply"])
    START >> req >> ask_ >> test >> out >> END

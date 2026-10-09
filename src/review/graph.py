"""propose_flow puts a simulation's option in the RM queue; review_flow records the RM's decision."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress

from review.ops import check_pending, decide, propose, read_decision, read_proposal


@graph
def review_flow(item_id, decision, note):
    """An RM approves or rejects a pending proposal."""
    pending = check_pending(item_id=item_id)
    done = decide(item_id=pending["item_id"], decision=decision, note=note)
    START >> pending >> done >> END


@graph
def propose_api():
    """POST {client_id, scenario, title, option, summary?} → the queued item."""
    req = ingress()
    ask = read_proposal(item=req["item"])
    queued = propose(client_id=ask["client_id"], kind=ask["kind"], title=ask["title"], data=ask["data"])
    out = egress(item=queued["item"])
    START >> req >> ask >> queued >> out >> END


@graph
def decide_api():
    """POST {item_id, decision, note?} → the decided item."""
    req = ingress()
    ask = read_decision(item=req["item"])
    done = review_flow(item_id=ask["item_id"], decision=ask["decision"], note=ask["note"])
    out = egress(item=done["item"])
    START >> req >> ask >> done >> out >> END

"""propose_flow puts a simulation's option in the RM queue; review_flow records the RM's decision.

Both are served as is (POST /api/review/propose, /api/review/decide): the body fills their
parameters."""

from operonx import END, START, graph

from review.ops import check_pending, decide, propose, read_decision, read_proposal


@graph
def propose_flow(client_id, option, scenario=None, title=None, summary=None):
    """A simulation's option, sent to the RM queue as a pending item."""
    ask = read_proposal(client_id=client_id, scenario=scenario, title=title, option=option, summary=summary)
    queued = propose(client_id=ask["client_id"], kind=ask["kind"], title=ask["title"], data=ask["data"])
    START >> ask >> queued >> END


@graph
def review_flow(item_id, decision, note=None):
    """An RM approves or rejects a pending proposal."""
    ask = read_decision(item_id=item_id, decision=decision, note=note)
    pending = check_pending(item_id=ask["item_id"])
    done = decide(item_id=pending["item_id"], decision=ask["decision"], note=ask["note"])
    START >> ask >> pending >> done >> END

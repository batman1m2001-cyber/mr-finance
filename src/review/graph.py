"""review_flow: the RM queue, one flow; a route picks its `action` (app/main.py binds it with `variants`, and
`bodies.py` is each route's request contract).

propose    POST /api/review/propose    a simulation's option, sent to the RM queue as a pending item
decide     POST /api/review/decide     an RM approves or rejects a pending proposal (the default action)
recommend  POST /api/review/recommend  the RM writes an action recommendation for a family (G-D7)"""

from operonx import END, START, graph
from operonx.core.ops import if_

from review.ops import check_pending, decide, propose, read_decision, read_proposal, recommend
from wealth.action import route


@graph
def review_flow(
    action="decide",
    client_id=None,
    option=None,
    scenario=None,
    title=None,
    summary=None,
    item_id=None,
    decision=None,
    note=None,
    by=None,
    actions=None,
):
    """A simulation's option for the RM, the RM's decision on it, or the RM's own recommendation."""
    which = route(action=action)
    proposal = read_proposal(client_id=client_id, scenario=scenario, title=title, option=option, summary=summary)
    queued = propose(client_id=proposal["client_id"], kind=proposal["kind"], title=proposal["title"], data=proposal["data"])
    ask = read_decision(item_id=item_id, decision=decision, note=note, by=by)
    pending = check_pending(item_id=ask["item_id"])
    done = decide(item_id=pending["item_id"], decision=ask["decision"], note=ask["note"], by=ask["by"])
    recommended = recommend(client_id=client_id, title=title, actions=actions, note=note, by=by)

    a = which["action"]
    START >> which >> if_(a == "propose", proposal).if_(a == "decide", ask).if_(a == "recommend", recommended).build()
    proposal >> queued >> END
    ask >> pending >> done >> END
    recommended >> END

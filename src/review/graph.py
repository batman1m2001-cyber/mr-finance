"""review_flow: the RM queue and the CIO's decisions, one flow; a route picks its `task` (app/main.py binds it with
`variants`, and `bodies.py` is each route's request contract). The selector is `task` because a view's or a run's
decision has a field named `action`.

propose    POST /api/review/propose    a simulation's option, sent to the RM queue as a pending item
decide     POST /api/review/decide     an RM approves or rejects a pending proposal (the default action)
recommend  POST /api/review/recommend  the RM writes an action recommendation for a family (G-D7)
view       POST /api/views/decide      the CIO edits, answers findings, approves, returns, rejects or withdraws (FR-304)
recompute  POST /api/runs/recompute    the run's view re-applied on today's data and compared (FR-405)
run        POST /api/runs/decide       the CIO makes a held run effective, or withdraws a run"""

from operonx import END, START, graph
from operonx.core.ops import if_

from apply.ops import decide_run, recompute
from review.ops import check_pending, decide, propose, read_decision, read_proposal, recommend
from views.ops import decide_view
from wealth.action import route


@graph
def review_flow(
    task="decide",
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
    view_id=None,
    action=None,
    reason="",
    idem_key=None,
    edits=None,
    responses=None,
    run=None,
):
    """A simulation's option for the RM, the RM's decision on it, the RM's own recommendation, or the CIO's decision on
    a view or a run."""
    which = route(action=task)
    proposal = read_proposal(client_id=client_id, scenario=scenario, title=title, option=option, summary=summary)
    queued = propose(client_id=proposal["client_id"], kind=proposal["kind"], title=proposal["title"], data=proposal["data"])
    ask = read_decision(item_id=item_id, decision=decision, note=note, by=by)
    pending = check_pending(item_id=ask["item_id"])
    done = decide(item_id=pending["item_id"], decision=ask["decision"], note=ask["note"], by=ask["by"])
    recommended = recommend(client_id=client_id, title=title, actions=actions, note=note, by=by)
    viewed = decide_view(
        view_id=view_id, action=action, by=by, reason=reason, idem_key=idem_key, edits=edits, responses=responses
    )
    recomputed = recompute(run_id=run, by=by, idem_key=idem_key)
    run_decided = decide_run(run_id=run, action=action, by=by, reason=reason)

    a = which["action"]
    START >> which >> if_(a == "propose", proposal).if_(a == "decide", ask).if_(a == "recommend", recommended).if_(
        a == "view", viewed
    ).if_(a == "recompute", recomputed).if_(a == "run", run_decided).build()
    proposal >> queued >> END
    ask >> pending >> done >> END
    recommended >> END
    viewed >> END
    recomputed >> END
    run_decided >> END

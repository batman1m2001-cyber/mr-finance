"""allocation_flow: one flow for the whole allocation feature, a route picks its `action` (app/main.py binds it with
`variants`, and `bodies.py` is each route's request contract).

view      POST /api/allocation          the household's holdings and profile → the case → three buckets, the actions
example   POST /api/allocation/example  the BRD's worked example K-7F3A
tilt      POST /api/allocation/tilt     a CIO tilts the model from an approved view
tilts     POST /api/allocation/tilts    the tilts in force and the model they give
send      POST /api/allocation/send     an RM sends the actions to the review queue
review    POST /api/allocation/review   the CIO decides each action (Q-29)
queue     POST /api/allocation/queue    the allocations waiting for the CIO
override  POST /api/allocation/override an RM moves an asset to another bucket
method    POST /api/allocation/method   the CIO picks ±2-point tilts or Black–Litterman"""

from operonx import END, START, graph
from operonx.core.ops import if_

from allocation.ops import allocate, case_of, check_request, example, override, queue, review, send, set_method, tilt, tilt_list
from consolidate.graph import consolidate_flow
from wealth.action import route


@graph
def allocation_flow(
    action="view",
    client_id=None,
    scope="family",
    method="A",
    assumptions=None,
    role=None,
    whatif=None,
    by=None,
    asset_class=None,
    stance=None,
    view_id=None,
    reason="",
    item_id=None,
    decisions=None,
    note="",
    key=None,
    bucket="",
):
    """Liquidity, Legacy and Growth for a client: each target, the gap, the fill and the rebalance, checked; with
    ``whatif``, the same for a scenario. The other actions are the CIO's and the RM's writes and reads."""
    which = route(action=action)
    ask = check_request(client_id=client_id, scope=scope, method=method, assumptions=assumptions, whatif=whatif)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    made = case_of(
        client_id=ask["client_id"], members=held["members"], holdings=held["holdings"], transactions=held["transactions"]
    )
    shown = allocate(case=made["case"], method=ask["method"], assumptions=ask["assumptions"], role=role, whatif=ask["whatif"])
    planned = allocate(case=made["case"], method=ask["method"], assumptions=ask["assumptions"], role="rm")
    sent = send(client_id=ask["client_id"], allocation=planned["allocation"], by=by)
    moved = override(client_id=ask["client_id"], holdings=held["holdings"], key=key, bucket=bucket, reason=reason, by=by)
    worked = example(method=method, assumptions=assumptions, role=role)
    tilted = tilt(asset_class=asset_class, stance=stance, view_id=view_id, reason=reason, by=by)
    tilts_in_force = tilt_list()
    decided = review(item_id=item_id, decisions=decisions, note=note, by=by)
    waiting = queue()
    picked = set_method(method=method, by=by)

    a = which["action"]
    START >> which >> if_(a == "example", worked).if_(a == "tilt", tilted).if_(a == "tilts", tilts_in_force).if_(
        a == "review", decided
    ).if_(a == "queue", waiting).if_(a == "method", picked).else_(ask)
    ask >> held >> if_(a == "override", moved).else_(made)
    made >> if_(a == "send", planned).else_(shown)
    planned >> sent
    shown >> END
    sent >> END
    moved >> END
    worked >> END
    tilted >> END
    tilts_in_force >> END
    decided >> END
    waiting >> END
    picked >> END

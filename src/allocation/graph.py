"""allocation_flow: the household's holdings and profile → the case → three buckets, their targets and the actions.

Served on POST /api/allocation (app/main.py), with the worked example (/api/allocation/example), the CIO's tilt
(/api/allocation/tilt) and an RM sending the actions to the review queue (/api/allocation/send)."""

from operonx import END, START, graph

from allocation.ops import allocate, case_of, check_request, example, send, tilt
from consolidate.graph import consolidate_flow


@graph
def allocation_flow(client_id, scope="family", method="A", assumptions=None, role=None):
    """Liquidity, Legacy and Growth for a client: each target, the gap, the fill and the rebalance, checked."""
    ask = check_request(client_id=client_id, scope=scope, method=method, assumptions=assumptions)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    made = case_of(
        client_id=ask["client_id"], members=held["members"], holdings=held["holdings"], transactions=held["transactions"]
    )
    out = allocate(case=made["case"], method=ask["method"], assumptions=ask["assumptions"], role=role)
    START >> ask >> held >> made >> out >> END


@graph
def allocation_example_flow(method="A", assumptions=None, role=None):
    """The BRD's worked example K-7F3A, the same numbers every time."""
    out = example(method=method, assumptions=assumptions, role=role)
    START >> out >> END


@graph
def allocation_tilt_flow(asset_class, stance, view_id, by, reason=""):
    """A CIO tilts the model portfolio from an approved view."""
    out = tilt(asset_class=asset_class, stance=stance, view_id=view_id, reason=reason, by=by)
    START >> out >> END


@graph
def allocation_send_flow(client_id, by, scope="family", method="A", assumptions=None):
    """An RM sends the allocation's actions (never a blocked one) to the review queue."""
    ask = check_request(client_id=client_id, scope=scope, method=method, assumptions=assumptions)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    made = case_of(
        client_id=ask["client_id"], members=held["members"], holdings=held["holdings"], transactions=held["transactions"]
    )
    out = allocate(case=made["case"], method=ask["method"], assumptions=ask["assumptions"], role="rm")
    sent = send(client_id=ask["client_id"], allocation=out["allocation"], by=by)
    START >> ask >> held >> made >> out >> sent >> END

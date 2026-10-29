"""allocation_flow: the household's holdings and profile → the case → three buckets, their targets and the actions.

Served on POST /api/allocation (app/main.py), with the worked example (/api/allocation/example), the CIO's tilt
(/api/allocation/tilt, read on /api/allocation/tilts) and an RM sending the actions to the review queue
(/api/allocation/send), the CIO deciding each action (/api/allocation/review) the CIO's page
(/api/allocation/queue) an RM's bucket override (/api/allocation/override)
and the CIO's pick of tilts or Black–Litterman (/api/allocation/method)."""

from operonx import END, START, graph

from allocation.ops import allocate, case_of, check_request, example, override, queue, review, send, set_method, tilt, tilt_list
from consolidate.graph import consolidate_flow


@graph
def allocation_flow(client_id, scope="family", method="A", assumptions=None, role=None, whatif=None):
    """Liquidity, Legacy and Growth for a client: each target, the gap, the fill and the rebalance, checked; with
    ``whatif``, the same for a scenario (money moved between Growth and Liquidity, spending changed)."""
    ask = check_request(client_id=client_id, scope=scope, method=method, assumptions=assumptions, whatif=whatif)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    made = case_of(
        client_id=ask["client_id"], members=held["members"], holdings=held["holdings"], transactions=held["transactions"]
    )
    out = allocate(case=made["case"], method=ask["method"], assumptions=ask["assumptions"], role=role, whatif=ask["whatif"])
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
def allocation_tilts_flow():
    """The CIO's tilts in force and the model they give each level."""
    out = tilt_list()
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


@graph
def allocation_review_flow(item_id, by, decisions=None, note=""):
    """The CIO approves or rejects each action of an allocation an RM sent (Q-29)."""
    out = review(item_id=item_id, decisions=decisions, note=note, by=by)
    START >> out >> END


@graph
def allocation_queue_flow():
    """The allocations waiting for the CIO and the last ones decided."""
    out = queue()
    START >> out >> END


@graph
def allocation_override_flow(client_id, key, by, bucket="", reason="", scope="family"):
    """An RM moves one asset of the household into another bucket, with a reason (§5)."""
    ask = check_request(client_id=client_id, scope=scope)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    out = override(client_id=ask["client_id"], holdings=held["holdings"], key=key, bucket=bucket, reason=reason, by=by)
    START >> ask >> held >> out >> END


@graph
def allocation_method_flow(method, by):
    """The CIO picks how the tilts move the model: ±2-point tilts or Black–Litterman."""
    out = set_method(method=method, by=by)
    START >> out >> END

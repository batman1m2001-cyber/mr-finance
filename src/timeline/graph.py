"""timeline_flow: one node's money over time (POST /api/timeline, docs/NODE_TIMELINE_PLAN.md T2)."""

from operonx import END, START, graph

from consolidate.graph import consolidate_flow
from timeline.ops import check_request, series


@graph
def timeline_flow(client_id, scope="personal", node="ME", unit="month"):
    """The node's value by day, month or year (a flow: its sums), from the simulated history since 2021."""
    ask = check_request(client_id=client_id, scope=scope, node=node, unit=unit)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    out = series(
        client_id=ask["client_id"],
        scope=ask["scope"],
        node=ask["node"],
        unit=ask["unit"],
        holdings=held["holdings"],
        members=held["members"],
        transactions=held["transactions"],
    )
    START >> ask >> held >> out >> END

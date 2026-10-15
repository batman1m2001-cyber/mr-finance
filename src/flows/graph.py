"""flows_flow: the consolidated transactions → one month's money in and out (POST /api/flows)."""

from operonx import END, START, graph

from consolidate.graph import consolidate_flow
from flows.ops import check_request, month_flows


@graph
def flows_flow(client_id, scope="personal", month=None):
    """Money Flow for a month (``month``: YYYY-MM; none = the latest month with rows)."""
    ask = check_request(client_id=client_id, scope=scope, month=month)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    out = month_flows(
        client_id=ask["client_id"],
        scope=ask["scope"],
        month=ask["month"],
        transactions=held["transactions"],
        members=held["members"],
    )
    START >> ask >> held >> out >> END

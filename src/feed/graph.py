"""feed_flow: the client's picture and transactions → the Intelligence Feed (POST /api/feed)."""

from operonx import END, START, graph

from consolidate.graph import consolidate_flow
from dashboard.graph import dashboard_flow
from feed.ops import check_request, feed


@graph
def feed_flow(client_id, scope="personal", role="client"):
    """What matters now for a client, why, and its evidence (``role``: client or rm)."""
    ask = check_request(client_id=client_id, scope=scope, role=role)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    dash = dashboard_flow(client_id=ask["client_id"], scope=ask["scope"])
    out = feed(
        client_id=ask["client_id"],
        scope=ask["scope"],
        role=ask["role"],
        dashboard=dash["dashboard"],
        transactions=held["transactions"],
    )
    START >> ask >> held >> dash >> out >> END

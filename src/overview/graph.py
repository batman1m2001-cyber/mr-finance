"""overview_flow: the client's whole picture as one graph (POST /api/overview, UI redesign R4)."""

from operonx import END, START, graph

from consolidate.graph import consolidate_flow
from dashboard.graph import dashboard_flow
from impact.ops import score
from overview.ops import build, check_request
from scenarios.ops import goals as goals_of
from scenarios.ops import profile_of


@graph
def overview_flow(client_id, scope="personal", role="client", goals=None):
    """Classes, holdings, sources, goals, risks, policy items and news events around one client (``goals``: the
    ids the client follows, as kept in the browser; None for the persona's defaults)."""
    ask = check_request(client_id=client_id, scope=scope, role=role, goals=goals)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    who = profile_of(client_id=ask["client_id"], members=held["members"])
    dash = dashboard_flow(client_id=ask["client_id"], scope=ask["scope"])
    mine = goals_of(client_id=ask["client_id"], holdings=held["holdings"], profile=who["profile"])
    found = score(holdings=held["holdings"], profile=who["profile"])
    out = build(
        client_id=ask["client_id"],
        scope=ask["scope"],
        role=ask["role"],
        followed=ask["followed"],
        dashboard=dash["dashboard"],
        goals=mine["goals"],
        alerts=found["alerts"],
    )
    START >> ask >> held >> who >> [dash, mine, found]
    [dash, mine, found] >> out >> END

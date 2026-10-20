"""overview_flow: the client's whole picture as one graph (POST /api/overview, UI redesign R4)."""

from operonx import END, START, graph

from consolidate.graph import consolidate_flow
from dashboard.graph import dashboard_flow
from flows.ops import month_flows
from impact.ops import score
from overview.ops import build, check_request
from scenarios.ops import goals as goals_of
from scenarios.ops import profile_of
from timeline.ops import changes


@graph
def overview_flow(client_id, scope="personal", role="client", goals=None):
    """Classes, holdings, sources, goals, risks, policy items, news events, the month's money in and out, the reserve
    and the stress scenarios around one client (``goals``: the ids the client follows, as kept in the browser; None
    for the persona's defaults). Each money node carries its change by day, month and year (src/timeline)."""
    ask = check_request(client_id=client_id, scope=scope, role=role, goals=goals)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    who = profile_of(client_id=ask["client_id"], members=held["members"])
    dash = dashboard_flow(client_id=ask["client_id"], scope=ask["scope"])
    mine = goals_of(client_id=ask["client_id"], holdings=held["holdings"], profile=who["profile"])
    found = score(holdings=held["holdings"], profile=who["profile"])
    money = month_flows(
        client_id=ask["client_id"],
        scope=ask["scope"],
        month="",
        transactions=held["transactions"],
        members=held["members"],
    )
    moved = changes(
        holdings=held["holdings"],
        members=held["members"],
        transactions=held["transactions"],
        month=money["flows"]["month"],
    )
    out = build(
        client_id=ask["client_id"],
        scope=ask["scope"],
        role=ask["role"],
        followed=ask["followed"],
        dashboard=dash["dashboard"],
        goals=mine["goals"],
        alerts=found["alerts"],
        flows=money["flows"],
        changes=moved["changes"],
    )
    START >> ask >> held >> who >> [dash, mine, found, money]
    money >> moved
    [dash, mine, found, moved] >> out >> END

"""pages_flow: one flow for the client's pages, a route picks its `action` (app/main.py binds it with `variants`,
and `bodies.py` is each route's request contract).

dashboard  POST /api/dashboard   the consolidated holdings, then every section of the page at once
overview   POST /api/overview    the client's whole picture as one graph (UI redesign R4)
timeline   POST /api/timeline    one node's money over time (docs/NODE_TIMELINE_PLAN.md T2)
flows      POST /api/flows       one month's money in and out
feed       POST /api/feed        the Intelligence Feed
feed_open  POST /api/feed/open   the client opened a high-level item (BRD-KPI-07)
search     POST /api/search      the header's search box
risk       POST /api/risk        one step of the adaptive risk test: the next question, or the result
contact    POST /api/rm/contacts an RM's contact with a family, recorded (BRD-KPI-06)

`dashboard_flow` stays a graph of its own: the dashboard, the overview and the feed all start from it, and it is
a subgraph here the way consolidate_flow is (docs/PLAN.md D9)."""

from operonx import END, START, graph
from operonx.core.ops import if_

from consolidate.graph import consolidate_flow
from contacts.ops import log_contact
from dashboard.graph import dashboard_flow
from feed.ops import check_request as check_feed
from feed.ops import feed, open_item
from flows.ops import check_request as check_flows
from flows.ops import month_flows
from impact.ops import score
from overview.ops import build
from overview.ops import check_request as check_overview
from risk.ops import ask as next_question
from risk.ops import check_request as check_risk
from risk.ops import context, next_step, reply, result
from scenarios.ops import goals as goals_of
from scenarios.ops import profile_of
from search.ops import check_request as check_search
from search.ops import search
from timeline.ops import changes
from timeline.ops import check_request as check_timeline
from timeline.ops import series
from wealth.action import route


@graph
def pages_flow(
    action="dashboard",
    client_id=None,
    scope="personal",
    months=12,
    role="client",
    goals=None,
    node="ME",
    unit="month",
    month=None,
    key=None,
    q=None,
    answers=None,
    family_id=None,
    channel="call",
    signal=None,
    note=None,
    by=None,
):
    """A client's pages. ``scope``: personal or family; ``role``: client or rm; ``month``: YYYY-MM (none = the latest
    month with rows); ``goals``: the ids the client follows, as kept in the browser."""
    which = route(action=action)

    # dashboard
    dashboard = dashboard_flow(client_id=client_id, scope=scope, months=months)

    # overview
    ask_overview = check_overview(client_id=client_id, scope=scope, role=role, goals=goals)
    held_overview = consolidate_flow(client_id=ask_overview["client_id"], scope=ask_overview["scope"])
    who_overview = profile_of(client_id=ask_overview["client_id"], members=held_overview["members"])
    dash_overview = dashboard_flow(client_id=ask_overview["client_id"], scope=ask_overview["scope"])
    mine_overview = goals_of(
        client_id=ask_overview["client_id"], holdings=held_overview["holdings"], profile=who_overview["profile"]
    )
    found_overview = score(holdings=held_overview["holdings"], profile=who_overview["profile"])
    money_overview = month_flows(
        client_id=ask_overview["client_id"],
        scope=ask_overview["scope"],
        month="",
        transactions=held_overview["transactions"],
        members=held_overview["members"],
    )
    moved_overview = changes(
        holdings=held_overview["holdings"],
        members=held_overview["members"],
        transactions=held_overview["transactions"],
        month=money_overview["flows"]["month"],
    )
    overview = build(
        client_id=ask_overview["client_id"],
        scope=ask_overview["scope"],
        role=ask_overview["role"],
        followed=ask_overview["followed"],
        dashboard=dash_overview["dashboard"],
        goals=mine_overview["goals"],
        alerts=found_overview["alerts"],
        flows=money_overview["flows"],
        changes=moved_overview["changes"],
    )

    # timeline
    ask_timeline = check_timeline(client_id=client_id, scope=scope, node=node, unit=unit)
    held_timeline = consolidate_flow(client_id=ask_timeline["client_id"], scope=ask_timeline["scope"])
    timeline = series(
        client_id=ask_timeline["client_id"],
        scope=ask_timeline["scope"],
        node=ask_timeline["node"],
        unit=ask_timeline["unit"],
        holdings=held_timeline["holdings"],
        members=held_timeline["members"],
        transactions=held_timeline["transactions"],
    )

    # flows
    ask_flows = check_flows(client_id=client_id, scope=scope, month=month)
    held_flows = consolidate_flow(client_id=ask_flows["client_id"], scope=ask_flows["scope"])
    flows = month_flows(
        client_id=ask_flows["client_id"],
        scope=ask_flows["scope"],
        month=ask_flows["month"],
        transactions=held_flows["transactions"],
        members=held_flows["members"],
    )

    # feed
    ask_feed = check_feed(client_id=client_id, scope=scope, role=role)
    held_feed = consolidate_flow(client_id=ask_feed["client_id"], scope=ask_feed["scope"])
    dash_feed = dashboard_flow(client_id=ask_feed["client_id"], scope=ask_feed["scope"])
    items = feed(
        client_id=ask_feed["client_id"],
        scope=ask_feed["scope"],
        role=ask_feed["role"],
        dashboard=dash_feed["dashboard"],
        transactions=held_feed["transactions"],
    )

    # feed_open
    opened = open_item(client_id=client_id, key=key)

    # search
    ask_search = check_search(q=q, role=role, client_id=client_id, scope=scope)
    held_search = consolidate_flow(client_id=ask_search["client_id"], scope=ask_search["scope"])
    who_search = profile_of(client_id=ask_search["client_id"], members=held_search["members"])
    mine_search = goals_of(
        client_id=ask_search["client_id"], holdings=held_search["holdings"], profile=who_search["profile"]
    )
    found = search(
        q=ask_search["q"], role=ask_search["role"], holdings=held_search["holdings"], goals=mine_search["goals"]
    )

    # risk
    checked = check_risk(client_id=client_id, answers=answers)
    held_risk = consolidate_flow(client_id=checked["client_id"], scope="personal")
    data = context(client_id=checked["client_id"], holdings=held_risk["holdings"], transactions=held_risk["transactions"])
    step = next_step(answers=checked["answers"], ctx=data["ctx"])
    asked = next_question(qid=step["qid"], answers=checked["answers"], ctx=data["ctx"])
    done = result(client_id=checked["client_id"], answers=checked["answers"], ctx=data["ctx"])
    risk = reply(asked=asked["reply"], done=done["reply"])

    # contact
    contact = log_contact(family_id=family_id, channel=channel, signal=signal, note=note, by=by)

    a = which["action"]
    START >> which >> if_(a == "dashboard", dashboard).if_(a == "overview", ask_overview).if_(
        a == "timeline", ask_timeline
    ).if_(a == "flows", ask_flows).if_(a == "feed", ask_feed).if_(a == "feed_open", opened).if_(
        a == "search", ask_search
    ).if_(a == "risk", checked).if_(a == "contact", contact).build()

    ask_overview >> held_overview >> who_overview >> [dash_overview, mine_overview, found_overview, money_overview]
    money_overview >> moved_overview
    [dash_overview, mine_overview, found_overview, moved_overview] >> overview
    ask_timeline >> held_timeline >> timeline
    ask_flows >> held_flows >> flows
    ask_feed >> held_feed >> dash_feed >> items
    ask_search >> held_search >> who_search >> mine_search >> found
    checked >> held_risk >> data >> step >> if_(step["done"] == True, done).else_(asked)  # noqa: E712
    asked >> risk
    done >> risk

    dashboard >> END
    overview >> END
    timeline >> END
    flows >> END
    items >> END
    opened >> END
    found >> END
    risk >> END
    contact >> END

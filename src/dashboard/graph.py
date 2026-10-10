"""dashboard_flow: the consolidated holdings, then every section of the page at once.

Served as is on POST /api/dashboard (app/main.py): the body fills its parameters."""

from operonx import END, START, graph

from consolidate.graph import consolidate_flow
from dashboard.ops import (
    allocation,
    assemble,
    cashflow,
    check_request,
    client_profile,
    concentration,
    drawdown,
    liquidity,
    net_worth,
    performance,
)


@graph
def dashboard_flow(client_id, scope="personal", months=12):
    """The whole picture of a client's wealth (``scope``: personal or family)."""
    ask = check_request(client_id=client_id, scope=scope, months=months)
    client_id, scope, months = ask["client_id"], ask["scope"], ask["months"]
    held = consolidate_flow(client_id=client_id, scope=scope)
    who = client_profile(client_id=client_id, members=held["members"])
    worth = net_worth(holdings=held["holdings"])
    mix = allocation(holdings=held["holdings"])
    pnl = performance(holdings=held["holdings"], realized_ytd=held["realized_ytd"], profile=who["profile"])
    risk = drawdown(holdings=held["holdings"], net_worth=worth["net_worth"], profile=who["profile"])
    spread = concentration(holdings=held["holdings"], net_worth=worth["net_worth"])
    reserve = liquidity(holdings=held["holdings"], profile=who["profile"])
    flows = cashflow(
        holdings=held["holdings"],
        transactions=held["transactions"],
        profile=who["profile"],
        months=months,
    )
    page = assemble(
        client_id=client_id,
        scope=scope,
        members=held["members"],
        waiting=held["waiting"],
        sources=held["sources"],
        holdings=held["holdings"],
        profile=who["profile"],
        net_worth=worth["net_worth"],
        allocation=mix["allocation"],
        performance=pnl["performance"],
        risk=risk["risk"],
        concentration=spread["concentration"],
        liquidity=reserve["liquidity"],
        cashflow=flows["cashflow"],
    )
    START >> ask >> held >> who >> [worth, mix, pnl, reserve, flows]
    worth >> [risk, spread]
    [mix, pnl, reserve, flows, risk, spread] >> page >> END

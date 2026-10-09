"""dashboard_flow: the consolidated holdings, then every section of the page at once.

dashboard_api is the same graph behind an HTTP door (app/main.py)."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress

from consolidate.graph import consolidate_flow
from dashboard.ops import (
    allocation,
    assemble,
    cashflow,
    client_profile,
    concentration,
    drawdown,
    liquidity,
    net_worth,
    performance,
    read_request,
)


@graph
def dashboard_flow(client_id, scope, months):
    """The whole picture of a client's wealth (``scope``: personal or family)."""
    held = consolidate_flow(client_id=client_id, scope=scope)
    who = client_profile(client_id=client_id, members=held["members"])
    worth = net_worth(holdings=held["holdings"])
    mix = allocation(holdings=held["holdings"])
    pnl = performance(
        holdings=held["holdings"], realized_ytd=held["realized_ytd"], profile=who["profile"]
    )
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
    START >> held >> who >> [worth, mix, pnl, reserve, flows]
    worth >> [risk, spread]
    [mix, pnl, reserve, flows, risk, spread] >> page >> END


@graph
def dashboard_api():
    """POST {client_id, scope?, months?} → the dashboard."""
    req = ingress()
    ask = read_request(item=req["item"])
    board = dashboard_flow(client_id=ask["client_id"], scope=ask["scope"], months=ask["months"])
    out = egress(item=board["dashboard"])
    START >> req >> ask >> board >> out >> END

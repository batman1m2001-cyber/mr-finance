"""consolidate_flow: who is in the picture, every source at once, one merged list."""

from operonx import END, START, graph

from consolidate.ops import (
    declared,
    household,
    merge_holdings,
    onehousing,
    open_api,
    statements,
    tcbs,
    techcom_capital,
    techcombank,
)


@graph
def consolidate_flow(client_id, scope):
    """Every holding of a client — or of their household — from tier 1, 2 and 3 sources."""
    who = household(client_id=client_id, scope=scope)
    bank = techcombank(members=who["members"])
    broker = tcbs(members=who["members"])
    funds = techcom_capital(members=who["members"])
    homes = onehousing(members=who["members"])
    other = open_api(members=who["members"])
    read = statements(members=who["members"])
    said = declared(members=who["members"])
    merged = merge_holdings(
        members=who["members"],
        waiting=who["waiting"],
        bank=bank["holdings"],
        broker=broker["holdings"],
        funds=funds["holdings"],
        homes=homes["holdings"],
        other=other["holdings"],
        read=read["holdings"],
        said=said["holdings"],
        transactions=bank["transactions"],
        realized_ytd=broker["realized_ytd"],
    )
    START >> who >> [bank, broker, funds, homes, other, read, said] >> merged >> END

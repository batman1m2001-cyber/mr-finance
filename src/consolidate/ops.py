"""The connectors and the merge.

Tier 1 (Techcombank, TCBS, Techcom Capital, OneHousing) needs nothing from the client; tier 2 is
another bank or broker over Open API, or a statement the client uploaded; tier 3 is what the
client declared. Each connector reads every household member who consented, and labels what it
returns with its trust: verified, statement or declared.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from operonx import op

from wealth import fixtures, store, valuation
from wealth.labels import SOURCES, TRUST

SCOPES = ("personal", "family")


@op
def household(client_id: str, scope: str = "personal") -> dict:
    """Whose assets this picture holds: the client, and in the family view every member who
    consented. Members who did not are listed, so the screen can say who is missing."""
    if scope not in SCOPES:
        raise ValueError(f"scope is one of {SCOPES}, not {scope!r}")
    me = fixtures.client(client_id)
    members = [{"id": me["id"], "name": me["name"], "relation": "Chủ tài khoản"}]
    waiting = []
    if scope == "family":
        for m in me.get("household", []):
            other = fixtures.client(m["id"])
            row = {"id": m["id"], "name": other["name"], "relation": m["relation"]}
            (members if m.get("consent") else waiting).append(row)
    return {"members": members, "waiting": waiting}


async def _each(members: List[Dict[str, Any]], read) -> List[Dict[str, Any]]:
    """One connector over every member, as the real API calls would go: at once."""
    await asyncio.sleep(0)
    out: List[Dict[str, Any]] = []
    for m in members:
        out.extend(read(m["id"], fixtures.client(m["id"])))
    return out


@op
async def techcombank(members: list) -> dict:
    """Deposits, cards, loans, and the account's transactions."""
    mk = fixtures.market()
    holdings = await _each(
        members, lambda mid, c: valuation.techcombank(mid, c["sources"]["techcombank"], mk)
    )
    tx = []
    for m in members:
        for t in fixtures.client(m["id"])["sources"]["techcombank"].get("transactions", []):
            tx.append({**t, "owner": m["id"]})
    return {"holdings": holdings, "transactions": tx}


@op
async def tcbs(members: list) -> dict:
    """Stocks and bonds at TCBS, and the profit already taken this year."""
    mk = fixtures.market()
    holdings = await _each(members, lambda mid, c: valuation.tcbs(mid, c["sources"]["tcbs"], mk))
    realized = sum(
        fixtures.client(m["id"])["sources"]["tcbs"].get("realized_ytd", 0) for m in members
    )
    return {"holdings": holdings, "realized_ytd": realized}


@op
async def techcom_capital(members: list) -> dict:
    """Fund certificates at Techcom Capital."""
    mk = fixtures.market()
    holdings = await _each(
        members, lambda mid, c: valuation.techcom_capital(mid, c["sources"]["techcom_capital"], mk)
    )
    return {"holdings": holdings}


@op
async def onehousing(members: list) -> dict:
    """Properties, valued by OneHousing's prices for their area."""
    mk = fixtures.market()
    holdings = await _each(
        members, lambda mid, c: valuation.onehousing(mid, c["sources"]["onehousing"], mk)
    )
    return {"holdings": holdings}


@op
async def open_api(members: list) -> dict:
    """Other banks and brokers the client let us read."""
    mk = fixtures.market()
    holdings = await _each(
        members, lambda mid, c: valuation.open_api(mid, c["sources"].get("open_api"), mk)
    )
    return {"holdings": holdings}


@op
async def statements(members: list) -> dict:
    """What the client's uploaded statements were read into (src/statements)."""
    holdings = await _each(members, lambda mid, c: store.holdings(mid, "statement"))
    return {"holdings": holdings}


@op
async def declared(members: list) -> dict:
    """What the client declared: in their file, and since, in the chat (src/declare)."""
    mk = fixtures.market()
    holdings = await _each(
        members,
        lambda mid, c: valuation.declared(
            mid, c.get("declared", []) + store.profile(mid, "asset"), mk
        ),
    )
    return {"holdings": holdings}


@op
def merge_holdings(
    members: list,
    waiting: list,
    bank: list,
    broker: list,
    funds: list,
    homes: list,
    other: list,
    read: list,
    said: list,
    transactions: list,
    realized_ytd: int = 0,
) -> dict:
    """One list, each holding once (a later copy of the same key replaces an earlier one), with
    every source's count, value and trust for the "Kết nối dữ liệu" screen."""
    names = {m["id"]: m["name"] for m in members}
    by_key: Dict[str, Dict[str, Any]] = {}
    for group in (bank, broker, funds, homes, other, read, said):
        for h in group:
            by_key[h["key"]] = {**h, "owner_name": names.get(h["owner"], h["owner"])}
    holdings = sorted(by_key.values(), key=lambda h: (h["kind"] != "asset", -h["value"]))
    sources = []
    for key, meta in SOURCES.items():
        mine = [h for h in holdings if h["source"] == key]
        trusts = sorted({h["trust"] for h in mine})
        sources.append(
            {
                "source": key,
                "label": meta["label"],
                "tier": meta["tier"],
                "what": meta["what"],
                "count": len(mine),
                "assets": sum(h["value"] for h in mine if h["kind"] == "asset"),
                "liabilities": sum(h["value"] for h in mine if h["kind"] == "liability"),
                "trust": [TRUST[t] for t in trusts],
                "status": "connected" if mine else "empty",
            }
        )
    return {
        "holdings": holdings,
        "sources": sources,
        "members": members,
        "waiting": waiting,
        "transactions": sorted(transactions, key=lambda t: t["date"]),
        "realized_ytd": realized_ytd,
    }

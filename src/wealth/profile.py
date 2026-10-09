"""The client's profile, as every picture measures against it: income, spending, the benchmark, the
drawdown they accept (from their last risk test, else their file), dependents and dated events —
summed over the household's members in the family view."""

from __future__ import annotations

from typing import Any, Dict, List

from wealth import fixtures, store


def build(client_id: str, members: List[Dict[str, Any]]) -> Dict[str, Any]:
    me = fixtures.client(client_id)
    ids = [m["id"] for m in members]
    people = [fixtures.client(i) for i in ids]
    test = store.result(client_id, "risk")
    events = []
    for p in people:
        events += [{**e, "owner": p["id"]} for e in p.get("events", [])]
        events += [{**e, "owner": p["id"]} for e in store.profile(p["id"], "event")]
    dependents = list(me.get("dependents", [])) + store.profile(client_id, "dependent")
    income_extra = sum(i.get("amount", 0) for p in people for i in store.profile(p["id"], "income"))
    return {
        "client_id": client_id,
        "name": me["name"],
        "age": me["age"],
        "occupation": me["occupation"],
        "segment": me["segment"],
        "persona_hint": me["persona_hint"],
        "income_monthly": sum(p.get("income_monthly", 0) for p in people) + income_extra,
        "spending_monthly": sum(p.get("spending_monthly", 0) for p in people),
        "benchmark": me.get("benchmark", "VNINDEX"),
        "drawdown_limit": (test or {}).get("drawdown_limit") or me.get("drawdown_limit", 0.15),
        "risk_persona": (test or {}).get("persona"),
        "risk_profile": ((test or {}).get("profile") or {}).get("name"),
        "dependents": dependents,
        "events": events,
    }

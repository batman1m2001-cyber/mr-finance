"""A client's labels (NEWS_EVIDENCE_BRD §7), read from what is on file, and the match: a client is touched when one of
its labels is one of the item's. No model here, so the same data gives the same matches."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, List

from procedural import goals


def of(holdings: List[Dict[str, Any]], client: Dict[str, Any], declared: Dict[str, Dict[str, Any]], today: date) -> Dict[str, Dict[str, Any]]:
    """label → where it came from: ``{"from": [names], "inferred": bool}``. A plan label read from a goal's name alone
    (not declared by the RM) is ``inferred``: it makes an RM task, never a client message (§7)."""
    out: Dict[str, Dict[str, Any]] = {}

    def add(label: str, name: str, inferred: bool = False) -> None:
        got = out.setdefault(label, {"from": [], "inferred": True})
        if name not in got["from"]:
            got["from"].append(name)
        got["inferred"] = got["inferred"] and inferred

    for h in holdings:
        d = h.get("detail") or {}
        if h["kind"] == "asset":
            add(f"asset:{h['class']}", h["name"])
            for k in ("sector", "ticker", "area"):
                if d.get(k):
                    add(f"{k}:{d[k]}", h["name"])
            if h["class"] == "stock":
                add("income:dividend", h["name"])
            if d.get("rental_monthly"):
                add("income:rent", h["name"])
        elif d.get("rate_type") == "floating":
            add("loan:floating", h["name"])
        if h["kind"] == "liability" and str(d.get("currency") or "VND").upper() != "VND":
            add("loan:fx", h["name"])
    if client.get("income_monthly"):
        add("income:salary", "Thu nhập hằng tháng")
    for g in goals.goals_of(client, today):
        dec = declared.get(g["goal_id"])
        got = dec or goals.infer(g["label"])
        if got:
            add(f"plan:{got['purpose']}", g["label"], inferred=not dec)
    return out


def match(targets: Iterable[str], labels: Dict[str, Dict[str, Any]]) -> List[str]:
    """The item's labels the client has, in the item's order."""
    return [t for t in targets if t in labels]

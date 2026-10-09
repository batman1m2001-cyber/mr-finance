"""The statement eval's check (app/main.py): did the reading find exactly what the file holds?"""

from __future__ import annotations

from typing import Any, Dict


def items_match(output: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    """Every stock with its quantity and every balance, nothing more; the institution named."""
    items = (output or {}).get("items") or []
    stocks = {i["ticker"]: round(i["qty"]) for i in items if i.get("type") == "stock"}
    balances = sorted(round(i["balance"]) for i in items if i.get("type") in ("cash", "deposit"))
    want_stocks = {k: round(v) for k, v in expected["stocks"].items()}
    want_balances = sorted(round(b) for b in expected["balances"])
    found = (output or {}).get("institution")
    reasons = []
    if stocks != want_stocks:
        reasons.append(f"stocks {stocks} != {want_stocks}")
    if balances != want_balances:
        reasons.append(f"balances {balances} != {want_balances}")
    if found != expected["institution"]:
        reasons.append(f"institution {found!r} != {expected['institution']!r}")
    hits = sum(1 for k, v in want_stocks.items() if stocks.get(k) == v) + sum(1 for b in want_balances if b in balances)
    total = len(want_stocks) + len(want_balances)
    return {"passed": not reasons, "score": hits / total if total else 1.0, "reason": "; ".join(reasons) or "all found"}

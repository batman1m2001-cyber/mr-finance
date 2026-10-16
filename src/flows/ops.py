"""The month's money in by category → out by category, and what was left (redesign kit K2, decision D4).

Only transaction rows: no inferred flow, no investment band (the fixtures hold no purchases). Every band is
the sum of its rows, and the rows come back with it, so a band opens to the payments it is made of.
"""

from __future__ import annotations

from typing import Any, Dict, List

from operonx import op

from control.errors import BadRequest
from wealth import fixtures

LABELS = {
    "salary": "Lương",
    "pension": "Lương hưu",
    "rent": "Tiền cho thuê",
    "living": "Chi tiêu sinh hoạt",
    "card": "Thanh toán thẻ",
    "loan": "Trả nợ vay",
    "school": "Học phí",
    "health": "Y tế",
    "rent_out": "Tiền thuê nhà",
}


@op
def check_request(client_id: str = None, scope: str = None, month: str = None) -> dict:
    """A known client, personal or family, and a month as YYYY-MM (or none: the latest with rows)."""
    client_id = str(client_id or "")
    if client_id not in fixtures.client_ids(members=True):
        raise BadRequest(f"no client {client_id!r}")
    scope = scope or "personal"
    if scope not in ("personal", "family"):
        raise ValueError("scope is personal or family")
    month = str(month or "")
    if month and (len(month) != 7 or month[4] != "-" or not (month[:4] + month[5:]).isdigit()):
        raise ValueError("month is YYYY-MM")
    return {"client_id": client_id, "scope": scope, "month": month}


def _side(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by: Dict[str, Dict[str, Any]] = {}
    for t in rows:
        c = t.get("category") or "other"
        b = by.setdefault(c, {"category": c, "label": LABELS.get(c, c), "amount": 0.0, "rows": []})
        b["amount"] += t["amount"]
        b["rows"].append(t)
    for b in by.values():
        b["rows"].sort(key=lambda t: (t["date"], t["desc"]))
    return sorted(by.values(), key=lambda b: -b["amount"])


@op
def month_flows(client_id: str, scope: str, month: str, transactions: list, members: list) -> dict:
    """In → out for one month, with the rows of every band and the months that have rows."""
    names = {m["id"]: m["name"] for m in members}
    rows = [
        {k: t[k] for k in ("date", "amount", "direction", "desc", "category")}
        | {"owner": t.get("owner"), "owner_name": names.get(t.get("owner"), "")}
        for t in transactions
    ]
    months = sorted({t["date"][:7] for t in rows})
    if month and month not in months:
        raise ValueError(f"không có giao dịch trong tháng {month}")
    month = month or (months[-1] if months else "")
    here = [t for t in rows if t["date"][:7] == month]
    inflow = _side([t for t in here if t["direction"] == "in"])
    outflow = _side([t for t in here if t["direction"] == "out"])
    total_in = sum(b["amount"] for b in inflow)
    total_out = sum(b["amount"] for b in outflow)
    return {
        "flows": {
            "client_id": client_id,
            "scope": scope,
            "month": month,
            "months": months,
            "members": [m["name"] for m in members],
            "inflow": inflow,
            "outflow": outflow,
            "total_in": total_in,
            "total_out": total_out,
            "left": total_in - total_out,  # negative: a shortfall (“Thiếu hụt”)
            "rows": len(here),
            "source": "giao dịch tài khoản Techcombank",
        }
    }

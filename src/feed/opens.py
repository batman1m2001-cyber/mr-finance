"""High-level alerts opened by clients (BRD-KPI-07 “khách mở cảnh báo mức cao ≥ 70%”; BRD_REMAINING_PLAN G7).

Nothing is sent to a client (BRD-RULE-SCOPE-05, ADR-0008): an alert reaches the client in the app, as a high-level
item of “Điều đáng chú ý” (the bell and Toàn cảnh, feed/ops.py). So:

- **Delivered** = the first time a high-level item is in a feed the client reads (as themselves: staff looking at
  the client's view deliver nothing).
- **Opened** = the client opens it: a click on the item in the bell, or on its evidence on Toàn cảnh.

Rate = opened ÷ delivered, by the month delivered (the latest month is still filling).
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from control import db
from people import auth

TARGET = 0.7  # BRD-KPI-07


def as_client() -> bool:
    """Whether the read is the client's own: the person signed in is a client (or, with no sign-in, the read asked
    for the client's view — tests and a local run)."""
    if not auth.checking():
        return True
    v = auth.signed_in()
    return bool(v) and v["role"] == "client"


def delivered(client_id: str, family_id: str, items: List[Dict[str, Any]]) -> int:
    """The high-level items of a feed the client read, kept the first time; how many were new."""
    high = [i for i in items if i["severity"] == "high"]
    if not high:
        return 0
    now = time.time()
    n = 0
    with db.tx() as con:
        for i in high:
            data = {"family_id": family_id, "type": i["type"], "evidence": i["evidence"]}
            cur = con.execute(
                "insert or ignore into client_alerts values (?, ?, ?, null, ?)",
                (client_id, i["key"], now, json.dumps(data, ensure_ascii=False)),
            )
            n += cur.rowcount
    return n


def opened(client_id: str, key: str) -> bool:
    """The client opened ``key``; False when it was never delivered to them or was opened before."""
    with db.tx() as con:
        cur = con.execute(
            "update client_alerts set opened = ? where client_id = ? and key = ? and opened is null",
            (time.time(), client_id, key),
        )
    return bool(cur.rowcount)


def rate() -> Dict[str, Any]:
    from measure.reports import _month, _stats

    with db.tx() as con:
        rows = [(r["first_shown"], r["opened"]) for r in con.execute("select first_shown, opened from client_alerts")]
    months = []
    for m in sorted({_month(s) for s, _ in rows}):
        mine = [(s, o) for s, o in rows if _month(s) == m]
        k = sum(1 for _, o in mine if o is not None)
        months.append(
            {
                "month": m,
                "delivered": len(mine),
                "opened": k,
                "share": round(k / len(mine), 3),
                "hours": _stats([(o - s) / 3600 for s, o in mine if o is not None]),
            }
        )
    return {"by_month": months, "target": TARGET}

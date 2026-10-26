"""Recommendations with a reviewer and a log (BRD-KPI-05 “khuyến nghị có người duyệt và nhật ký: 100%”;
BRD_REMAINING_PLAN G7), read from the records the product keeps.

What the product delivers as a recommendation (our reading, labelled “Đề xuất”):

- **an application run made effective** — the RMs and clients read its impact. Reviewer: the person who
  approved the view (the decision it was applied from). Log: the approval and the run becoming effective, both
  in the audit chain.
- **a newsletter approved** — a second CIO's approval of the author's letter (Compliance's before OWN-FB-18).
  Reviewer: the approver, never the author. Log: the approval in the audit chain.
- **an RM queue item approved** — an option the client proposed, or a recommendation the RM wrote, approved by the
  RM (FEAT-27; before OWN-FB-18 by the family's certified specialist when it had one). Reviewer: the specialist on
  those older items, else the RM who decided. Log: the decisions in the audit chain (recorded from G7; earlier
  decisions name no one). An RM's own recommendation approved by that RM alone has no second person and is counted
  as a miss.

A recommendation counts when its reviewer is a person on the staff list (not an agent, not the system), other
than its author, and its log entries are in the chain. Each one that does not is listed with what is missing.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set, Tuple

from control import db, roles
from measure.reports import _month

TARGET = 1.0  # BRD-KPI-05


def _logged(con) -> Set[Tuple[str, str]]:
    """``(action, object)`` pairs in the audit chain; a run's status change as ``run.status:<to>``."""
    out = set()
    for r in con.execute(
        "select action, object, data from audit_log where action in "
        "('decision.approve', 'run.status', 'newsletter.approve', 'review.decide', 'review.specialist')"
    ):
        action = r["action"]
        if action == "run.status":
            action += ":" + str(json.loads(r["data"]).get("to"))
        out.add((action, r["object"]))
    return out


def _check(reviewer: Optional[str], author: Optional[str], need: List[Tuple[str, str]], logged) -> List[str]:
    missing = []
    staff = roles.users()
    if not reviewer or reviewer not in staff:
        missing.append("không có người duyệt")
    elif reviewer == author:
        missing.append("người duyệt là người soạn")
    if any(n not in logged for n in need):
        missing.append("thiếu nhật ký")
    return missing


def rows() -> List[Dict[str, Any]]:
    from wealth import store as wealth

    wealth.reviews()  # the RM queue's table is the wealth store's (made on its first use)
    out = []
    with db.tx() as con:
        logged = _logged(con)
        decisions = {r["id"]: db.load(r) for r in con.execute("select * from decisions")}
        for r in con.execute("select id, data from application_runs"):
            run = db.load(r)
            eff = next((h for h in run.get("history", []) if h.get("status") == "EFFECTIVE"), None)
            if eff is None:
                continue
            dec = decisions.get(run.get("decision_id") or "") or {}
            need = [("decision.approve", dec.get("id") or "?"), ("run.status:EFFECTIVE", run["id"])]
            # the view's text is the agent's; the CIO who approves it is its reviewer
            out.append(("run", run["id"], eff["at"], dec.get("by"), None, need))
        for r in con.execute("select id, data from newsletters where status = 'APPROVED'"):
            n = db.load(r)
            at = next((h["at"] for h in reversed(n["history"]) if h["status"] == "APPROVED"), None)
            out.append(
                ("newsletter", n["id"], at, n.get("approved_by"), n.get("author"), [("newsletter.approve", n["id"])])
            )
    for item in wealth.reviews(status="approved"):
        d = item["data"]
        need = [("review.decide", item["id"])] + ([("review.specialist", item["id"])] if d.get("specialist_by") else [])
        # the reviewer: the certified specialist when one approved (G8), else the RM; an RM's own recommendation
        # approved by that RM alone has no second person
        reviewer = d.get("specialist_by") or d.get("decided_by")
        out.append(("rm_item", item["id"], item["decided"], reviewer, d.get("author"), need))
    result = []
    for kind, rid, at, reviewer, author, need in out:
        missing = _check(reviewer, author, need, logged)
        result.append(
            {
                "kind": kind,
                "id": rid,
                "month": _month(at) if at else None,
                "reviewer": reviewer,
                "missing": missing,
                "ok": not missing,
            }
        )
    return sorted(result, key=lambda x: (x["month"] or "", x["id"]))


KIND = {"run": "Lần áp dụng hiệu lực", "newsletter": "Bản tin đã duyệt", "rm_item": "Đề xuất RM đã duyệt"}


def rate() -> Dict[str, Any]:
    rs = rows()
    months = []
    for m in sorted({r["month"] for r in rs if r["month"]}):
        mine = [r for r in rs if r["month"] == m]
        ok = sum(r["ok"] for r in mine)
        months.append(
            {
                "month": m,
                "recommendations": len(mine),
                "ok": ok,
                "share": round(ok / len(mine), 3),
                "by_kind": {k: sum(1 for r in mine if r["kind"] == k) for k in KIND},
            }
        )
    misses = [{**r, "kind_label": KIND[r["kind"]]} for r in reversed(rs) if not r["ok"]][:30]
    return {"by_month": months, "misses": misses, "target": TARGET, "kinds": KIND}

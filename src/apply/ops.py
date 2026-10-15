"""The steps of re-applying a view (FR-405) and of the CIO's decision on a held run."""

from __future__ import annotations

import uuid
from typing import Optional

from operonx import op

from apply import run as runs
from control import roles
from views import store as vstore


@op
async def recompute(run_id: str, by: str = "cio", idem_key: Optional[str] = None) -> dict:
    """Thẩm định lại: the same approved view on today's holdings and prices → a new run, compared
    with the old one family by family."""
    roles.require(by, "cio")
    old = runs.get(str(run_id))
    view = vstore.get(old["view_id"])
    new = await runs.apply_view(view, by, old["decision_id"], idem_key or f"recompute:{run_id}:{uuid.uuid4().hex}")
    before = {r["family_id"]: r["expected_3m"] for r in old.get("ranking", [])}
    compare = [
        {
            "family_id": r["family_id"],
            "name": r["name"],
            "before": before.get(r["family_id"]),
            "after": r["expected_3m"],
            "delta": r["expected_3m"] - before.get(r["family_id"], 0),
        }
        for r in new.get("ranking", [])
    ]
    return {"run": new, "compare": compare}


@op
def decide_run(run_id: str, action: str, by: str, reason: str = "") -> dict:
    """make_effective (a run post-check held) or withdraw, with a reason."""
    roles.require(by, "cio")
    if len(str(reason or "").strip()) < 5:
        raise ValueError("Cần lý do (từ 5 ký tự)")
    return {"run": runs.decide_run(str(run_id), action, by, str(reason).strip())}

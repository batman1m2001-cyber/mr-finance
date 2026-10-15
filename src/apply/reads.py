"""What each role reads of the results (FR-502, A7, §14).

- CIO: every run, with post-check findings.
- RM: runs that passed post-check only — effective, superseded, withdrawn, each labelled.
- Client: effective runs only, by asset class (no ticker, no holding, no action word), with the
  labels flow 2 requires: AI-assisted, not a recommendation, who is responsible, when.
"""

from __future__ import annotations

from typing import Any, Dict, List

from apply import run as runs
from control import roles
from events import store as events
from news.ops import config as news_config
from views import schema
from views import store as vstore

CLIENT_NOTE = (
    "Nội dung có sự hỗ trợ của AI, do CIO duyệt kịch bản; đây là ước tính theo mô hình với tham số giả định, "
    "không phải khuyến nghị đầu tư. Liên hệ chuyên viên quan hệ khách hàng nếu cần trao đổi."
)
VISIBLE = {"cio": None, "admin": None, "compliance": None, "rm": runs.RM_VISIBLE, "client": ("EFFECTIVE",)}


def family_impact(family_id: str, role: str) -> Dict[str, Any]:
    if role not in VISIBLE:
        raise roles.Forbidden(f"vai trò {role!r} không có")
    statuses = VISIBLE[role]
    items: List[Dict[str, Any]] = []
    for run in runs.runs(statuses=statuses):
        try:
            r = runs.family_result(run["id"], family_id)
        except KeyError:
            continue
        view = vstore.get(run["view_id"])
        ev = events.get(run["event_id"])
        h3 = r["horizons"]["3m"]
        item = {
            "run_id": run["id"],
            "status": run["status"],
            "status_label": run["status_label"],
            "event": {"id": ev["id"], "title": ev["title"] if role != "client" else _type_label(ev.get("type"))},
            "view_id": view["id"],
            "approved_at": next((x["at"] for x in reversed(view["history"]) if x["status"] == "APPROVED"), None),
            "price_date": run.get("price_date"),
            "model": run.get("model"),
            "net_worth": r["net_worth"],
            "horizons": {
                k: {x: v[x] for x in ("expected", "p5", "p10", "p50", "p90")} for k, v in r["horizons"].items()
            },
            "pct": r["pct"],
            "by_class": h3["by_class"],
            "classes": {k: schema.ASSET_CLASSES.get(k, k) for k in h3["by_class"]},
            "modelled_share": r["modelled_share"],
        }
        if role != "client":  # the view's text may name tickers: staff only (flow 2)
            item["summary"] = view["current"]["summary"]
            item.update(
                by_factor=h3["by_factor"],
                holdings=[{**x, "contribution": h3["by_holding"].get(x["key"], 0)} for x in r["holdings"]],
                pre_review=r["pre_review"],
                loan_interest_3m=r["loan_interest_3m"],
            )
        if role in ("cio", "admin", "compliance"):
            item["postcheck"] = [f for f in run["postcheck"]["findings"] if f["family_id"] in (None, family_id)]
        items.append(item)
    effective = [i for i in items if i["status"] == "EFFECTIVE"]
    out = {
        "family_id": family_id,
        "role": role,
        "items": items,
        "effective_expected_3m": sum(i["horizons"]["3m"]["expected"] for i in effective),
        "effective_count": len(effective),
    }
    if role == "client":
        cio = roles.USERS["cio"]
        out["labels"] = {"note": CLIENT_NOTE, "responsible": f"{cio['name']} — {cio['title']}", "ai": "AI hỗ trợ"}
    return out


def _type_label(event_type: str | None) -> str:
    """A client reads the kind of event, not the headline: a headline may name a company (flow 2)."""
    labels = {t["id"]: t["label"] for t in news_config()["event_types"]}
    return labels.get(event_type or "", "Sự kiện thị trường")


def rm_today() -> Dict[str, Any]:
    """The RM's first list (BRD step 7): families flagged for pre-review in effective runs, worst first."""
    cases = []
    for run in runs.runs(statuses=("EFFECTIVE",)):
        ev = events.get(run["event_id"])
        for row in run.get("ranking", []):
            if row["pre_review"]:
                cases.append({**row, "run_id": run["id"], "event": {"id": ev["id"], "title": ev["title"]}})
    cases.sort(key=lambda c: (c["p10_3m_pct"], c["family_id"]))
    from research.ops import matches

    tasks = [m for m in matches() if m["level"] in ("contact_now", "confirm_goal", "remind")]
    return {"cases": cases, "threshold_pct": runs.PRE_REVIEW_PCT, "goal_tasks": tasks}

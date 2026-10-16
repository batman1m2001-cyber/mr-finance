"""What each role reads of the results (FR-502, A7, §14).

- CIO: every run, with post-check findings.
- RM: runs that passed post-check only — effective, superseded, withdrawn, each labelled.
- Client: effective runs only, by asset class (no ticker, no holding, no action word), with the
  labels flow 2 requires: AI-assisted, not a recommendation, who is responsible, when.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from apply import run as runs
from control import roles
from events import store as events
from news.ops import config as news_config
from research import conflict
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
    labels = schema.class_labels()
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
            "classes": {k: labels.get(k, k) for k in h3["by_class"]},
            "modelled_share": r["modelled_share"],
            "goal_impact": r.get("goal_impact"),  # FR-404; absent on runs computed before it
        }
        item["timeline"] = _timeline(ev, view, run)
        outlets = sorted({n.get("outlet") or "Nguồn công khai" for n in ev.get("news") or []})
        item["sources"] = {"outlets": outlets, "count": len(ev.get("news") or [])}  # RULE-CONTENT-02, no headline
        item["conflicts"] = [  # CONTENT-02: the research behind the event that concerns a related party, disclosed
            conflict.disclosure(n["conflict"]) for n in ev.get("news") or [] if (n.get("conflict") or {}).get("related")
        ]
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
        cio = roles.users()["cio"]
        out["labels"] = {
            "note": CLIENT_NOTE,
            "responsible": f"{cio['name']} — {cio['title']}",
            "ai": "AI hỗ trợ",
            "conflicts": sorted({c for i in items for c in i["conflicts"]}) or [conflict.NONE],
        }
    return out


VIEW_STEP = {"DRAFTING": "AI soạn nhận định", "PENDING_CHALLENGE": "AI phản biện", "APPROVED": "CIO duyệt"}
RUN_STEP = {
    "COMPUTING": "Áp dụng cho các gia đình",
    "EFFECTIVE": "Có hiệu lực",
    "SUPERSEDED": "Bị thay thế",
    "WITHDRAWN": "Bị rút lại",
    "NEEDS_CIO_REVIEW": "Chờ CIO xem lại",
    "FAILED": "Lỗi",
}


def _timeline(ev: Dict[str, Any], view: Dict[str, Any], run: Dict[str, Any]) -> List[Dict[str, Any]]:
    """An event's way to the family, each step with its time, read from the stored records (UI redesign R4: the
    timeline on Tin tác động): the first news, the event, the view's draft, challenge and approval, the run."""
    out: List[Dict[str, Any]] = []
    published = [n["published"] for n in ev.get("news") or [] if n.get("published")]
    if published:
        out.append({"at": min(published), "step": "news", "label": "Tin đầu tiên", "source": "event"})
    out.append({"at": ev["created"], "step": "event", "label": "Gom thành sự kiện", "source": "event"})
    for h in view.get("history") or []:
        if h["status"] in VIEW_STEP:
            out.append({"at": h["at"], "step": h["status"].lower(), "label": VIEW_STEP[h["status"]], "source": "view"})
    for h in run.get("history") or []:
        if h["status"] in RUN_STEP:
            out.append({"at": h["at"], "step": h["status"].lower(), "label": RUN_STEP[h["status"]], "source": "run"})
    return sorted(out, key=lambda x: x["at"])


def _type_label(event_type: str | None) -> str:
    """A client reads the kind of event, not the headline: a headline may name a company (flow 2)."""
    labels = {t["id"]: t["label"] for t in news_config()["event_types"]}
    return labels.get(event_type or "", "Sự kiện thị trường")


def rm_today(families: Optional[List[str]] = None) -> Dict[str, Any]:
    """The RM's first list (BRD step 7): families flagged for pre-review in effective runs, worst first. With
    ``families``, only those (an RM sees the families assigned to them, BRD-RULE-ROLE-02)."""
    keep = None if families is None else set(families)
    cases = []
    for run in runs.runs(statuses=("EFFECTIVE",)):
        ev = events.get(run["event_id"])
        for row in run.get("ranking", []):
            if row["pre_review"] and (keep is None or row["family_id"] in keep):
                cases.append({**row, "run_id": run["id"], "event": {"id": ev["id"], "title": ev["title"]}})
    cases.sort(key=lambda c: (c["p10_3m_pct"], c["family_id"]))
    from research.ops import matches

    tasks = [
        m
        for m in matches()
        if m["level"] in ("contact_now", "confirm_goal", "remind") and (keep is None or m["family_id"] in keep)
    ]
    from contacts import store as contacts
    from control import config
    from wealth import fixtures

    for c in cases:  # what an RM's contact cites as the signal it started from (BRD-KPI-06)
        c["signal"] = f"pre_review:{c['run_id']}"
    for t in tasks:
        t["signal"] = f"goal:{t['note_id']}:{t['goal_id']}"
    mine = sorted(keep) if keep is not None else fixtures.client_ids()
    return {
        "cases": cases,
        "threshold_pct": config.data("thresholds")["pre_review_pct"],
        "goal_tasks": tasks,
        "contacts": contacts.recent(mine),
        "families": [{"id": f, "name": fixtures.client(f)["name"]} for f in mine],
        "channels": contacts.CHANNELS,
    }

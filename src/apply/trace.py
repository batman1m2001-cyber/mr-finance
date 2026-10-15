"""FR-406 / BR-12: from one number of a family back to the news it came from.

number → the holdings behind it (value, loadings, method) → each branch (probability, core shocks,
the factor moves the engine propagated, the family's change in that branch) → the view the CIO
approved (who, when, why; the challenger's findings and the CIO's answers) → the event → the news
items (outlet, link, published time) → the snapshot (hash, price date, model, engine).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from apply import run as runs
from engine import FactorModel, propagate
from engine.scenario import Branch
from events import store as events
from views import store as vstore

HORIZON_LABEL = {"1w": "1 tuần", "3m": "3 tháng", "12m": "12 tháng"}

FORMULA = (
    "Tác động kỳ vọng = Σ theo nhánh (xác suất × Σ theo vị thế (giá trị × Σ theo yếu tố (độ nhạy × tỷ lệ thể hiện "
    "theo kỳ hạn × biến động của yếu tố trong nhánh))). Biến động yếu tố: cú sốc lõi do CIO duyệt, các yếu tố khác "
    "suy ra bằng kỳ vọng có điều kiện trên ma trận hiệp phương sai của chế độ."
)


def trace(run_id: str, family_id: str, key: Optional[str] = None, horizon: str = "3m") -> Dict[str, Any]:
    run = runs.get(run_id)
    fam = runs.family_result(run_id, family_id)
    snap = runs.snapshot(run["snapshot_id"])
    model = FactorModel.from_dict(snap["factor_model"])
    h = fam["horizons"][horizon]

    holdings = [x for x in fam["holdings"] if x["loads"]]
    if key and key in model.ids:  # a factor's contribution
        number = {"label": f"Đóng góp của {model.factor(key).name}", "value": h["by_factor"].get(key, 0)}
        holdings = [x for x in holdings if key in x["loads"]]
    elif key and key in h["by_class"]:  # an asset class
        number = {"label": f"Đóng góp của nhóm {key}", "value": h["by_class"][key]}
        holdings = [x for x in holdings if x["class"] == key]
    elif key:  # one holding
        number = {"label": "Đóng góp của vị thế", "value": h["by_holding"].get(key, 0)}
        holdings = [x for x in fam["holdings"] if x["key"] == key]
    else:
        number = {"label": f"Tác động kỳ vọng {HORIZON_LABEL.get(horizon, horizon)}", "value": h["expected"]}
    nw = fam["net_worth"]
    number.update(
        horizon=horizon, pct=number["value"] / nw if nw else 0.0, band={x: h[x] for x in ("p5", "p10", "p50", "p90")}
    )

    branches = []
    fam_branch = {b["id"]: b for b in h["branches"]}
    for b in snap["branches"]:
        p = propagate(Branch.from_dict({**b, "probability": 1.0}), model)
        branches.append(
            {
                "id": b["id"],
                "name": b["name"],
                "probability": b["probability"],
                "regime": b["regime"],
                "core": [
                    {"factor": s["factor"], "direction": s["direction"], "size": s["size"], "priced_in": s["priced_in"]}
                    for s in b["shocks"]
                ],
                "moves": {f.id: round(m, 4) for f, m in zip(model.factors, p.moves) if abs(m) > 1e-9},
                "family_expected": fam_branch.get(b["id"], {}).get("expected"),
            }
        )

    view = vstore.get(run["view_id"])
    approve = next((d for d in reversed(vstore.decisions(view["id"])) if d["action"] == "approve"), None)
    ch = vstore.latest_challenge(view["id"])
    ev = events.get(view["event_id"])
    return {
        "run": {"id": run_id, "status": run["status"], "status_label": run["status_label"]},
        "family": {"id": family_id, "name": fam["name"], "net_worth": nw, "pre_review": fam["pre_review"]},
        "number": number,
        "formula": FORMULA,
        "holdings": [{**x, "contribution": h["by_holding"].get(x["key"], 0)} for x in holdings],
        "branches": branches,
        "view": {
            "id": view["id"],
            "summary": view["current"]["summary"],
            "content_hash": view["content_hash"],
            "mode": view["mode"],
            "models": view["models"],
        },
        "approval": approve and {k: approve.get(k) for k in ("id", "by", "reason", "created")},
        "challenge": ch
        and {
            "id": ch["id"],
            "model": ch["model"],
            "findings": ch["findings"],
            "responses": (view.get("responses") or {}).get(ch["id"], {}),
        },
        "event": {"id": ev["id"], "title": ev["title"]},
        "news": [
            {k: n.get(k) for k in ("id", "title", "url", "outlet", "section", "published", "label")} for n in ev["news"]
        ],
        "snapshot": {
            "id": snap["id"],
            "hash": snap["hash"],
            "price_date": snap["market"]["as_of"],
            "market_sha256": snap["market"]["sha256"],
            "model": run["model"],
            "engine_version": snap["engine_version"],
        },
    }

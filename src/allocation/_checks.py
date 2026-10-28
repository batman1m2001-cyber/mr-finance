"""The suitability check of each allocation action (ASSET_ALLOCATION_BRD §9): BLOCK, WARN or PASS, with the reasons.

BLOCK (never shown to the client, the reason kept for the RM): it raises a class above what the client's level
allows, adds to a class the client excluded, makes one position more than the concentration limit of all assets, or
leaves Liquidity short, or its words are the forbidden recommendation phrases.
WARN (shown with the warning): a holding of its class is already over the concentration limit, the risk test is
older than 12 months, or the risk level is simulated.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from allocation import _model


def check(case: Dict[str, Any], a: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    from views.schema import forbidden_words

    block: List[str] = []
    warn: List[str] = []
    level = int(case["risk"]["level"])
    limit = _model.data()["concentration"]
    assets = a["reconcile"]["assets"] or 1
    cls = action.get("class")
    model = a["model"]["classes"].get(cls) if cls else None
    if action["kind"] == "buy" and model:
        total = a["growth"]["rebalance"]["total"] or 1
        if model["target"] == 0 or a["growth"]["rebalance"]["after"][cls] / total > model["high"] + 1e-9:
            block.append(f"Tăng {model['label'].lower()} quá mức rủi ro {level} của khách")
        if cls in (case.get("excluded") or []):
            block.append(f"Khách đã loại trừ {model['label'].lower()}")
        if action["amount"] / assets > limit:
            block.append(f"Một vị thế vượt ngưỡng tập trung {limit:.0%} tổng tài sản")
    if action["moves"].get("liquidity") and a["liquidity"]["after"] + action["moves"]["liquidity"] < a["liquidity"]["target"]:
        block.append("Làm giỏ Thanh khoản thiếu")
    words = forbidden_words(f"{action['what']} {action['why']}")
    if words:
        block.append("Chứa cụm từ cấm: " + ", ".join(words))
    if cls:
        mine = [
            h
            for h in case["holdings"]
            if h["kind"] == "asset" and h["class"] not in ("cash", "deposit", "real_estate", "business", "insurance")
            and _model.model_class(h, level) == cls and h["value"] / assets > limit
        ]
        if mine:
            warn.append(f"Đang vượt ngưỡng tập trung {limit:.0%} từ trước")
    risk = case["risk"]
    if risk.get("source") == "simulated":
        warn.append("Hồ sơ giả lập")
    elif risk.get("at"):
        taken = date.fromisoformat(str(risk["at"])[:10])
        now = date.fromisoformat(str(case["as_of"])[:10])
        if (now - taken).days > 365:
            warn.append("Kết quả bài test quá 12 tháng")
    status = "BLOCK" if block else "WARN" if warn else "PASS"
    return {"status": status, "reasons": block or warn}

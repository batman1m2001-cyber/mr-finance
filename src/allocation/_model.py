"""The Growth bucket's model portfolio and the CIO's tilt (ASSET_ALLOCATION_BRD §7).

``data/model_portfolio.json`` (written by scripts/make_fixtures.py) holds, per risk level 1–5, each class's target and
allowed range, the expected return of each class, and the other assumptions the CIO sets. A tilt is the CIO's
Tăng / Trung lập / Giảm on a class: ±2 points each, at most ±5 in all per class, kept inside the range, and the
difference goes to (or comes from) cash waiting to be invested so the model still sums to 100 %.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

PATH = Path(__file__).resolve().parents[2] / "data" / "model_portfolio.json"
CLASSES = ("cash", "bond", "equity", "gold", "crypto")
LABELS = {
    "cash": "Tiền chờ đầu tư",
    "bond": "Trái phiếu",
    "equity": "Cổ phiếu & quỹ",
    "gold": "Vàng",
    "crypto": "Tài sản số",
}
STANCES = {"overweight": +1, "neutral": 0, "underweight": -1}
STANCE_LABELS = {"overweight": "Tăng tỷ trọng", "neutral": "Trung lập", "underweight": "Giảm tỷ trọng"}


@lru_cache(maxsize=1)
def data() -> Dict[str, Any]:
    return json.loads(PATH.read_text(encoding="utf-8"))


def model_class(holding: Dict[str, Any], level: int) -> str:
    """Which model class a Growth holding counts as: a bond fund with bonds, a money fund with cash, crypto with
    equity at levels 4–5 (its own class, target 0, below)."""
    cls = holding["class"]
    if cls == "fund":
        kind = (holding.get("detail") or {}).get("fund_type")
        return {"bond": "bond", "money": "cash"}.get(kind, "equity")
    if cls == "crypto":
        return "equity" if level >= 4 else "crypto"
    return {"stock": "equity", "bond": "bond", "gold": "gold", "cash": "cash", "deposit": "cash"}.get(cls, "equity")


def base(level: int) -> Dict[str, Dict[str, float]]:
    """The level's untilted model: {class: {target, low, high}} in fractions; crypto 0 at levels 1–3."""
    row = data()["levels"][str(level)]
    out = {c: {"target": v[0] / 100, "low": v[1] / 100, "high": v[2] / 100} for c, v in row["classes"].items()}
    if level < 4:
        out["crypto"] = {"target": 0.0, "low": 0.0, "high": 0.0}
    return out


def tilted(level: int, tilts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The model after the CIO's tilts: {classes: {c: {target, low, high, base, tilt, views}}, applied: [...]}."""
    model = base(level)
    step, cap = data()["tilt"]["step"] / 100, data()["tilt"]["cap"] / 100
    moved = {c: 0.0 for c in model}
    views: Dict[str, List[str]] = {c: [] for c in model}
    applied = []
    for t in tilts:
        c = t.get("asset_class")
        if c not in model or c == "crypto" or STANCES.get(t.get("stance"), 0) == 0:
            continue
        want = moved[c] + STANCES[t["stance"]] * step
        want = max(-cap, min(cap, want))
        lo, hi = model[c]["low"] - model[c]["target"], model[c]["high"] - model[c]["target"]
        want = max(lo, min(hi, want))
        if abs(want - moved[c]) < 1e-9:
            continue
        moved[c] = want
        if t.get("view"):
            views[c].append(t["view"])
        applied.append({**t, "label": STANCE_LABELS[t["stance"]], "class_label": LABELS[c]})
    # the other classes' change goes to (or comes from) cash waiting to be invested; a tilt on cash alone comes
    # from (or goes to) the other classes in proportion to their targets
    others = [c for c in model if c not in ("cash", "crypto")]
    s = sum(moved[c] for c in others)
    if abs(s) > 1e-9:
        moved["cash"] = -s
    elif abs(moved["cash"]) > 1e-9:
        weight = sum(model[c]["target"] for c in others)
        for c in others:
            moved[c] = -moved["cash"] * model[c]["target"] / weight
    inside = all(model[c]["low"] - 1e-9 <= model[c]["target"] + moved[c] <= model[c]["high"] + 1e-9 for c in model)
    if not inside:  # cash could not take it inside its range: back to the untilted model
        moved = {c: 0.0 for c in model}
        views = {c: [] for c in model}
        applied = []
    classes = {
        c: {
            "target": round(model[c]["target"] + moved[c], 6),
            "low": model[c]["low"],
            "high": model[c]["high"],
            "base": model[c]["target"],
            "tilt": round(moved[c], 6),
            "views": views[c],
            "label": LABELS[c],
        }
        for c in model
    }
    return {"classes": classes, "applied": applied}


def expected_return(classes: Dict[str, Dict[str, Any]]) -> float:
    """Σ weight × the class's assumed return (crypto at the equity rate)."""
    r = data()["expected_return"]
    return sum(v["target"] * r.get(c, r["equity"]) for c, v in classes.items())

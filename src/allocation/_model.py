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
METHODS = {"tilt": "Nghiêng ±2 điểm", "bl": "Black–Litterman"}


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


def black_litterman(level: int, tilts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The model after the same tilts read as Black–Litterman views; the same shape as ``tilted``."""
    import numpy as np

    bl = data()["black_litterman"]
    model = base(level)
    step = tilted(level, tilts)  # the tilts that apply (a crypto or neutral one does not), their views and labels
    risky = [c for c in ("cash", "bond", "equity", "gold")]
    w = np.array([model[c]["target"] for c in risky])
    vol = np.array([bl["vol"][c] for c in risky])
    corr = np.eye(len(risky))
    for pair, rho in bl["corr"].items():
        a, b = (risky.index(x) for x in pair.split("|"))
        corr[a, b] = corr[b, a] = rho
    sigma = corr * np.outer(vol, vol)
    pi = bl["delta"] * sigma @ w  # the returns the level's model is right for
    net = {c: 0 for c in risky}
    for t in step["applied"]:
        net[t["asset_class"]] += STANCES[t["stance"]]
    rows = [c for c in risky if net[c]]
    if rows:
        P = np.array([[1.0 if c == r else 0.0 for c in risky] for r in rows])
        Q = P @ pi + np.array([net[r] * bl["view"] for r in rows])
        ts = bl["tau"] * sigma
        omega = np.diag(np.diag(P @ ts @ P.T))
        a = np.linalg.inv(ts) + P.T @ np.linalg.inv(omega) @ P
        mu = np.linalg.solve(a, np.linalg.inv(ts) @ pi + P.T @ np.linalg.inv(omega) @ Q)
        want = np.linalg.solve(bl["delta"] * sigma, mu)
    else:
        want = w
    cap = data()["tilt"]["cap"] / 100  # the same guard as the tilts: at most ±5 points a class
    move = {c: max(-cap, min(cap, float(want[i] - w[i]))) for i, c in enumerate(risky) if c != "cash"}

    def placed(k: float) -> Dict[str, float]:
        out = {c: min(model[c]["high"], max(model[c]["low"], model[c]["target"] + k * d)) for c, d in move.items()}
        out["cash"] = 1.0 - sum(out.values())
        return out

    k, got = 1.0, placed(1.0)
    if not model["cash"]["low"] - 1e-9 <= got["cash"] <= model["cash"]["high"] + 1e-9:  # less of the move, cash in range
        lo, hi = 0.0, 1.0
        for _ in range(40):
            k = (lo + hi) / 2
            got = placed(k)
            lo, hi = (k, hi) if model["cash"]["low"] - 1e-9 <= got["cash"] <= model["cash"]["high"] + 1e-9 else (lo, k)
        k, got = lo, placed(lo)
    classes = {}
    for c, m in model.items():
        target = got.get(c, m["target"])
        classes[c] = {
            "target": round(target, 6),
            "low": m["low"],
            "high": m["high"],
            "base": m["target"],
            "tilt": round(target - m["target"], 6),
            "views": step["classes"][c]["views"],
            "label": LABELS[c],
        }
    return {"classes": classes, "applied": step["applied"], "method": "bl", "scaled": round(k, 4)}


def model_for(level: int, tilts: List[Dict[str, Any]], method: str = "tilt") -> Dict[str, Any]:
    """The model in force: the ±2-point tilts or Black–Litterman."""
    if method == "bl":
        return black_litterman(level, tilts)
    return {**tilted(level, tilts), "method": "tilt"}


# P2: the model read by the 11 asset classes the news labels use (NEWS_EVIDENCE_BRD §7) — a second view of the same
# household and the same Growth model, not a second model
ELEVEN = {
    "vn_equity": "Cổ phiếu Việt Nam",
    "foreign_equity": "Cổ phiếu nước ngoài",
    "bond": "Trái phiếu",
    "fund": "Chứng chỉ quỹ",
    "gold": "Vàng",
    "crypto": "Tài sản số",
    "fx": "Ngoại tệ",
    "real_estate": "Bất động sản",
    "private_equity": "Cổ phần doanh nghiệp",
    "usd_loan": "Vay ngoại tệ",
    "floating_loan": "Vay lãi thả nổi",
}
LOANS = ("usd_loan", "floating_loan")


def _foreign(detail: Dict[str, Any]) -> bool:
    return (detail.get("currency") or "VND").upper() != "VND" or (detail.get("market") or "VN").upper() != "VN"


def eleven_class(holding: Dict[str, Any]) -> str | None:
    """Which of the 11 classes a holding is; None for what none of them is (VND cash and deposits, a money fund,
    insurance, a fixed-rate VND loan)."""
    cls, d = holding["class"], holding.get("detail") or {}
    if holding.get("kind") == "liability":
        if (d.get("currency") or "VND").upper() != "VND":
            return "usd_loan"
        return "floating_loan" if d.get("rate_type") == "floating" else None
    if cls == "stock":
        return "foreign_equity" if _foreign(d) else "vn_equity"
    if cls == "fund":
        return None if d.get("fund_type") == "money" else "fund"
    if cls in ("cash", "deposit"):
        return "fx" if _foreign(d) else None
    return {"bond": "bond", "gold": "gold", "crypto": "crypto", "real_estate": "real_estate",
            "business": "private_equity"}.get(cls)


def eleven(holdings: List[Dict[str, Any]], growth: List[Dict[str, Any]], model: Dict[str, Any],
           growth_total: float) -> Dict[str, Any]:
    """The household by the 11 classes: each row's value, what of it sits in Growth, and the Growth model's target
    for the row (a Growth class's target split by the CIO's ``eleven.split``; no target for the rows Growth does
    not hold). ``outside`` is what is in none of the 11."""
    split = data()["eleven"]["split"]
    target = {k: 0.0 for k in ELEVEN}
    has_target = set()
    for c, m in model["classes"].items():
        for k, share in (split.get(c) or {}).items():
            target[k] += m["target"] * share
            has_target.add(k)
    value = {k: 0.0 for k in ELEVEN}
    in_growth = {k: 0.0 for k in ELEVEN}
    outside = 0.0
    for h in holdings:
        k = eleven_class(h)
        if k is None:
            outside += h["value"] if h.get("kind") == "asset" else 0.0
        else:
            value[k] += h["value"]
    for h in growth:
        k = eleven_class(h)
        if k:
            in_growth[k] += h["value"]
    rows = [
        {
            "key": k,
            "label": label,
            "loan": k in LOANS,
            "value": value[k],
            "in_growth": in_growth[k],
            "target_pct": round(target[k], 6) if k in has_target else None,
            "target": target[k] * growth_total if k in has_target else None,
        }
        for k, label in ELEVEN.items()
    ]
    return {"rows": rows, "outside": outside, "growth_total": growth_total}

"""What the CIO agent may hand back (BRD §8.2), checked before anything is saved (§8.3).

The catalogue the agent picks from is market knowledge only — asset classes, sectors, tickers, the
exchange rate, the engine's 15 factors and their S / M / L library. No client data is in it.
``check(view, news_ids, ...)`` returns every problem as a sentence; an empty list means valid.
Impact rows that name a ticker on the restricted list are taken out and kept aside, not refused.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from engine import default_model
from wealth import fixtures

ASSET_CLASSES = {
    "stock": "Cổ phiếu",
    "bond": "Trái phiếu",
    "fund": "Chứng chỉ quỹ",
    "gold": "Vàng",
    "crypto": "Tiền số",
    "real_estate": "Bất động sản",
    "deposit": "Tiền gửi",
    "cash": "Tiền mặt",
    "business": "Cổ phần tư nhân",
    "insurance": "Bảo hiểm",
    "fx": "Ngoại tệ",
}
TARGET_TYPES = ("asset_class", "sector", "ticker", "fx")
HORIZONS = ("1w", "3m", "12m")
CONFIDENCE = ("low", "medium", "high")
PRICED_IN = ("none", "partial", "full")
REGIMES = ("normal", "stressed")
SEVERITIES = ("critical", "medium", "low")

# words a view must not use: it is market analysis, not advice to buy or sell (§8.2, F18). Version 1 of the
# forbidden_phrases configuration (``recommendation``); Compliance changes it there.
FORBIDDEN = [
    "nên mua",
    "nên bán",
    "mua vào",
    "bán ra",
    "khuyến nghị mua",
    "khuyến nghị bán",
    "chốt lời",
    "cắt lỗ",
    "gom hàng",
    "bắt đáy",
    "xuống tiền",
    "all in",
    "tất tay",
]
_VIETNAMESE = re.compile(r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", re.IGNORECASE)


def class_labels() -> Dict[str, str]:
    """Every asset class's label: the built-in ones and those declared in the factor model (NFR-06)."""
    extra = default_model().loadings.get("classes") or {}
    return {**ASSET_CLASSES, **{k: v["label"] for k, v in extra.items()}}


def catalogue() -> Dict[str, Any]:
    """What the agent may name: market knowledge only."""
    m = fixtures.market()
    model = default_model()
    return {
        "asset_class": class_labels(),
        "sector": sorted({v["sector"] for v in m["stocks"].values()} | {v["sector"] for v in m["bonds"].values()}),
        "ticker": {t: {"sector": v["sector"], "issuer": v["issuer"]} for t, v in sorted(m["stocks"].items())},
        "fx": ["USDVND"],
        "factors": [
            {"id": f.id, "name": f.name, "unit": f.unit, "sizes": f.sizes, "group": f.group} for f in model.factors
        ],
        "model_version": model.version,
    }


_PATTERNS: Dict[str, Any] = {}


def phrases_pattern(which: str) -> "re.Pattern[str]":
    """The ``forbidden_phrases`` list in force (Compliance's configuration; ``FORBIDDEN`` above is its version 1)
    as one pattern, rebuilt when a new version comes into force."""
    from control import config

    key = (which, config.active_hash("forbidden_phrases"))
    if key not in _PATTERNS:
        words = config.data("forbidden_phrases")[which]
        _PATTERNS[key] = re.compile(r"(?<!\w)(" + "|".join(re.escape(w) for w in words) + r")(?!\w)", re.IGNORECASE)
    return _PATTERNS[key]


def forbidden_words(text: str) -> List[str]:
    return sorted({m.group(0).lower() for m in phrases_pattern("recommendation").finditer(text or "")})


def split_restricted(impacts: List[Dict[str, Any]], restricted_tickers: List[str]) -> Tuple[list, list]:
    keep, out = [], []
    blocked = {t.upper() for t in restricted_tickers}
    for row in impacts:
        if row.get("target_type") == "ticker" and str(row.get("target", "")).upper() in blocked:
            out.append(row)
        else:
            keep.append(row)
    return keep, out


STRESS_CORE = {"VNINDEX", "RE_SPREAD"}


def check(view: Dict[str, Any], news_ids: List[str], agent: bool = True) -> List[str]:
    """Every way ``view`` breaks §8.2; [] when it is valid. ``agent``: the agent's answer, which also obeys the
    prompt rule AI-05; a CIO's edit does not — the challenger raises it as a critical finding (R2) the CIO answers."""
    errs: List[str] = []
    cat = catalogue()
    factor_ids = {f["id"] for f in cat["factors"]}
    news = set(news_ids)

    summary = view.get("summary")
    if not isinstance(summary, str) or len(summary.strip()) < 20:
        errs.append("summary: cần tóm tắt từ 20 ký tự")
    else:
        if not _VIETNAMESE.search(summary):
            errs.append("summary: phải viết bằng tiếng Việt")
        if forbidden_words(summary):
            errs.append(f"summary: có từ ngữ khuyến nghị mua/bán: {', '.join(forbidden_words(summary))}")

    impacts = view.get("impacts")
    if not isinstance(impacts, list) or not impacts:
        errs.append("impacts: cần ít nhất một dòng tác động")
        impacts = []
    for i, row in enumerate(impacts):
        where = f"impacts[{i}]"
        if not isinstance(row, dict):
            errs.append(f"{where}: phải là một đối tượng")
            continue
        tt, target = row.get("target_type"), row.get("target")
        if tt not in TARGET_TYPES:
            errs.append(f"{where}.target_type: phải là một trong {', '.join(TARGET_TYPES)}")
        elif tt == "asset_class" and target not in cat["asset_class"]:
            errs.append(f"{where}.target: loại tài sản {target!r} không có trong danh mục")
        elif tt == "sector" and target not in cat["sector"]:
            errs.append(f"{where}.target: ngành {target!r} không có trong danh mục")
        elif tt == "ticker" and target not in cat["ticker"]:
            errs.append(f"{where}.target: mã {target!r} không có trong danh mục")
        elif tt == "fx" and target not in cat["fx"]:
            errs.append(f"{where}.target: tỷ giá {target!r} không có trong danh mục")
        level = row.get("level")
        if not isinstance(level, int) or isinstance(level, bool) or not -3 <= level <= 3:
            errs.append(f"{where}.level: số nguyên từ −3 đến +3")
        if row.get("horizon") not in HORIZONS:
            errs.append(f"{where}.horizon: một trong {', '.join(HORIZONS)}")
        if row.get("confidence") not in CONFIDENCE:
            errs.append(f"{where}.confidence: một trong {', '.join(CONFIDENCE)}")
        if not isinstance(row.get("rationale"), str) or len(row["rationale"].strip()) < 10:
            errs.append(f"{where}.rationale: cần lập luận")
        elif forbidden_words(row["rationale"]):
            errs.append(f"{where}.rationale: có từ ngữ khuyến nghị mua/bán")
        errs += _sources(where, row.get("source_ids"), news)

    sc = view.get("scenarios")
    if not isinstance(sc, dict):
        return errs + ["scenarios: thiếu bộ kịch bản"]
    if sc.get("priced_in") not in PRICED_IN:
        errs.append(f"scenarios.priced_in: một trong {', '.join(PRICED_IN)}")
    branches = sc.get("branches")
    if not isinstance(branches, list) or not 2 <= len(branches) <= 4:
        return errs + ["scenarios.branches: cần 2–4 nhánh"]
    total = 0.0
    ids = set()
    for i, b in enumerate(branches):
        where = f"branches[{i}]"
        if not isinstance(b, dict):
            errs.append(f"{where}: phải là một đối tượng")
            continue
        bid = b.get("id")
        if not isinstance(bid, str) or not bid or bid in ids:
            errs.append(f"{where}.id: cần mã nhánh riêng")
        ids.add(bid)
        if not isinstance(b.get("name"), str) or not b["name"].strip():
            errs.append(f"{where}.name: cần tên nhánh")
        p = b.get("probability")
        if not isinstance(p, (int, float)) or isinstance(p, bool) or not 0.05 <= p <= 0.95:
            errs.append(f"{where}.probability: từ 0,05 đến 0,95")
        else:
            total += float(p)
        if b.get("regime") not in REGIMES:
            errs.append(f"{where}.regime: normal hoặc stressed")
        shocks = b.get("core_shocks")
        if not isinstance(shocks, list) or not 1 <= len(shocks) <= 5:
            errs.append(f"{where}.core_shocks: 1–5 cú sốc lõi")
            shocks = []
        seen = set()
        for j, s in enumerate(shocks):
            w = f"{where}.core_shocks[{j}]"
            if not isinstance(s, dict):
                errs.append(f"{w}: phải là một đối tượng")
                continue
            if s.get("factor") not in factor_ids:
                errs.append(f"{w}.factor: {s.get('factor')!r} không thuộc 15 yếu tố")
            elif s["factor"] in seen:
                errs.append(f"{w}.factor: {s['factor']} lặp lại trong nhánh")
            seen.add(s.get("factor"))
            if s.get("direction") not in ("up", "down"):
                errs.append(f"{w}.direction: up hoặc down")
            if s.get("size") not in ("S", "M", "L"):
                errs.append(f"{w}.size: S, M hoặc L")
        if agent and b.get("regime") == "stressed" and not STRESS_CORE <= seen:
            # BRD-RULE-AI-05 (§8.1, the 2022 back-test): enforced on the agent's answer, not only asked in the prompt
            missing = ", ".join(sorted(STRESS_CORE - seen))
            errs.append(f"{where}.core_shocks: nhánh căng thẳng phải có VNINDEX và RE_SPREAD (thiếu {missing})")
        if not isinstance(b.get("rationale"), str) or len(b["rationale"].strip()) < 20:
            errs.append(f"{where}.rationale: lập luận từ 20 ký tự")
        elif forbidden_words(b["rationale"]):
            errs.append(f"{where}.rationale: có từ ngữ khuyến nghị mua/bán")
        errs += _sources(where, b.get("source_ids"), news)
    if total and abs(total - 1.0) > 0.011:
        errs.append(f"scenarios.branches: tổng xác suất {total:.3f}, phải là 1 ± 0,011")
    return errs


def _sources(where: str, ids: Any, news: set) -> List[str]:
    if not isinstance(ids, list) or not ids:
        return [f"{where}.source_ids: cần ít nhất một tin nguồn"]
    bad = [i for i in ids if i not in news]
    return [f"{where}.source_ids: {', '.join(map(str, bad))} không thuộc sự kiện"] if bad else []


def to_engine(branches: List[Dict[str, Any]], priced_in: str) -> List[Dict[str, Any]]:
    """The view's branches as the engine reads them (probabilities renormalised to exactly 1: the
    schema allows ± 0.011)."""
    total = sum(float(b["probability"]) for b in branches)
    return [
        {
            "id": b["id"],
            "name": b["name"],
            "probability": float(b["probability"]) / total,
            "regime": b["regime"],
            "shocks": [
                {
                    "factor": s["factor"],
                    "direction": 1 if s["direction"] == "up" else -1,
                    "size": s["size"],
                    "priced_in": priced_in,
                }
                for s in b["core_shocks"]
            ],
        }
        for b in branches
    ]

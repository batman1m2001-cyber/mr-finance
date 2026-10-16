"""The CIO agent's mock mode (BRD §8.4): scenarios from keywords, no model.

For tests and for a demo without a model key. Every output says it is a mock. It reads only the
event's news and the catalogue, like the live agent: the direction of each factor comes from the
words around its keyword in the headlines ("tăng", "giảm", "hạ"...), the size from how many items
agree, and the stressed branch always carries VN-Index and real-estate credit as core shocks (the
BRD's prompt rule, learnt from 2022).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

LENSES = {
    "macro": {"label": "Vĩ mô và lãi suất", "factors": ["VN_RATE", "VN_GOV", "USDVND", "US10Y", "DXY"]},
    "equity": {"label": "Cổ phiếu và quỹ", "factors": ["VNINDEX", "GLOBAL_EQ", "FOREIGN_FLOW"]},
    "credit": {"label": "Tín dụng và bất động sản", "factors": ["RE_SPREAD", "FIN_SPREAD", "VN_HOUSE"]},
    "other": {"label": "Hàng hóa và tài sản khác", "factors": ["GOLD", "SJC_GAP", "BTC", "BRENT"]},
}

UP = [
    "tăng",
    "lên",
    "cao",
    "vượt",
    "bứt phá",
    "phục hồi",
    "đi lên",
    "leo",
    "nâng",
    "mua ròng",
    "rise",
    "raise",
    "higher",
    "hike",
    "gain",
]
DOWN = [
    "giảm",
    "hạ",
    "lao dốc",
    "xuống",
    "thấp",
    "sụt",
    "lùi",
    "rơi",
    "bán ròng",
    "mất",
    "cut",
    "lower",
    "fall",
    "drop",
    "decline",
]
_UP = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, UP)) + r")(?!\w)")
_DOWN = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, DOWN)) + r")(?!\w)")

# a factor's move → which way each target moves (the sign of the engine's loading)
EFFECTS = {
    "VNINDEX": [("asset_class", "stock", 1), ("asset_class", "fund", 1)],
    "GLOBAL_EQ": [("asset_class", "stock", 1)],
    "FOREIGN_FLOW": [("asset_class", "stock", 1)],
    "GOLD": [("asset_class", "gold", 1)],
    "SJC_GAP": [("asset_class", "gold", 1)],
    "BTC": [("asset_class", "crypto", 1)],
    "USDVND": [("fx", "USDVND", 1), ("ticker", "FPT", 1)],
    "VN_RATE": [("asset_class", "bond", -1), ("asset_class", "real_estate", -1), ("sector", "Bất động sản", -1)],
    "VN_GOV": [("asset_class", "bond", -1)],
    "RE_SPREAD": [("sector", "Bất động sản", -1), ("asset_class", "real_estate", -1)],
    "FIN_SPREAD": [("sector", "Ngân hàng", -1)],
    "VN_HOUSE": [("asset_class", "real_estate", 1)],
    "US10Y": [("asset_class", "bond", -1)],
    "DXY": [("fx", "USDVND", 1)],
    "BRENT": [("sector", "Hóa chất", 1)],
}

DEFAULT_FACTOR = {  # an event whose headlines name no factor
    "monetary": "VN_RATE",
    "fx": "USDVND",
    "gold": "GOLD",
    "credit": "RE_SPREAD",
    "real_estate": "VN_HOUSE",
    "commodity": "BRENT",
    "crypto": "BTC",
    "equity": "VNINDEX",
}

NOTE = "Mô phỏng (không dùng AI)"


def _direction(text: str, words: List[str]) -> int:
    """+1 / −1 / 0: the up and down words within a short window around the factor's keywords."""
    votes = 0
    for w in words:
        for m in re.finditer(rf"(?<!\w){re.escape(w)}(?!\w)", text):
            window = text[max(0, m.start() - 25) : m.end() + 40]
            votes += len(_UP.findall(window)) - len(_DOWN.findall(window))
    return (votes > 0) - (votes < 0)


def factor_votes(news: List[Dict[str, Any]], factor_words: Dict[str, List[str]]) -> Dict[str, Tuple[int, List[str]]]:
    """factor → (net direction votes over the items, the items that name it)."""
    out: Dict[str, Tuple[int, List[str]]] = {}
    for it in news:
        text = f"{it['title']} {it.get('summary', '')}".lower()
        for f in it.get("factors", []):
            d = _direction(text, factor_words.get(f, []))
            v, ids = out.get(f, (0, []))
            out[f] = (v + d, ids + [it["id"]])
    return out


def analyst(
    lens: str, news: List[Dict[str, Any]], factor_words: Dict[str, List[str]], spec: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """One analyst group's note: its factors' directions and the impact rows they imply. ``spec``: the group as
    the prompts configuration declares it (label, factors); the BRD's four by default."""
    spec = spec or LENSES[lens]
    votes = factor_votes(news, factor_words)
    mine = {f: votes[f] for f in spec["factors"] if f in votes}
    rows = []
    for f, (v, ids) in mine.items():
        if v == 0:
            continue
        level = max(-3, min(3, v))
        for tt, target, sign in EFFECTS.get(f, []):
            rows.append(
                {
                    "target_type": tt,
                    "target": target,
                    "level": sign * level,
                    "horizon": "3m",
                    "confidence": "low",
                    "rationale": f"{NOTE}: {len(ids)} tin cho thấy yếu tố {f} {'tăng' if v > 0 else 'giảm'}.",
                    "source_ids": sorted(set(ids)),
                    "factor": f,
                }
            )
    return {
        "lens": lens,
        "label": spec["label"],
        "factors": {f: {"votes": v, "source_ids": sorted(set(ids))} for f, (v, ids) in mine.items()},
        "impacts": rows,
        "note": NOTE,
    }


def needs_debate(notes: List[Dict[str, Any]]) -> bool:
    """BRD 8.1: a bull/bear debate only when a row reaches ±2 or the groups disagree on a target."""
    seen: Dict[Tuple[str, str], int] = {}
    for n in notes:
        for r in n["impacts"]:
            if abs(r["level"]) >= 2:
                return True
            key = (r["target_type"], r["target"])
            s = (r["level"] > 0) - (r["level"] < 0)
            if key in seen and seen[key] != s:
                return True
            seen[key] = s
    return False


def debate(notes: List[Dict[str, Any]], rounds: int = 1) -> Dict[str, Any]:
    """The rows merged by target: levels summed and capped, the larger side kept."""
    merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for n in notes:
        for r in n["impacts"]:
            key = (r["target_type"], r["target"])
            if key in merged:
                m = merged[key]
                m["level"] = max(-3, min(3, m["level"] + r["level"]))
                m["source_ids"] = sorted(set(m["source_ids"]) | set(r["source_ids"]))
            else:
                merged[key] = dict(r)
    rows = [r for r in merged.values() if r["level"] != 0]
    return {
        "rounds": rounds,
        "impacts": rows,
        "bull": [f"{r['target']} {r['level']:+d}" for r in rows if r["level"] > 0],
        "bear": [f"{r['target']} {r['level']:+d}" for r in rows if r["level"] < 0],
        "note": NOTE,
    }


def synthesize(
    event: Dict[str, Any],
    news: List[Dict[str, Any]],
    notes: List[Dict[str, Any]],
    merged: Dict[str, Any],
    factor_names: Dict[str, str],
) -> Dict[str, Any]:
    """The view: summary, impact rows, and three branches (base, the reverse, the stressed one)."""
    ids = [n["id"] for n in news]
    votes: Dict[str, Tuple[int, List[str]]] = {}
    for n in notes:
        for f, v in n["factors"].items():
            votes[f] = (v["votes"], v["source_ids"])
    ranked = sorted((f for f in votes if votes[f][0] != 0), key=lambda f: (-abs(votes[f][0]), f))[:3]
    if not ranked:
        f = DEFAULT_FACTOR.get(event.get("type") or "", "VNINDEX")
        votes[f] = (-1, ids)
        ranked = [f]
    top = ranked[0]

    def shock(f: str, sign: int, size: str) -> Dict[str, Any]:
        return {"factor": f, "direction": "up" if sign > 0 else "down", "size": size}

    base = [shock(f, votes[f][0], "M" if abs(votes[f][0]) >= 2 else "S") for f in ranked]
    reverse = [shock(top, -votes[top][0], "S")]
    stressed = [shock("VNINDEX", -1, "L"), shock("RE_SPREAD", 1, "M")]
    if top not in ("VNINDEX", "RE_SPREAD"):
        # the adverse side of the main factor: the way that hurts a typical holder of its asset
        stressed.append(shock(top, _adverse(top), "L"))
    word = {1: "tăng", -1: "giảm"}
    main = ", ".join(f"{factor_names.get(f, f)} {word[(votes[f][0] > 0) - (votes[f][0] < 0)]}" for f in ranked)
    impacts = [{k: v for k, v in r.items() if k != "factor"} for r in merged["impacts"]]
    if not impacts:
        for tt, target, sign in EFFECTS.get(top, [("asset_class", "stock", 1)]):
            impacts.append(
                {
                    "target_type": tt,
                    "target": target,
                    "level": sign * (1 if votes[top][0] > 0 else -1),
                    "horizon": "3m",
                    "confidence": "low",
                    "rationale": f"{NOTE}: suy từ loại sự kiện.",
                    "source_ids": ids,
                }
            )
    return {
        "summary": (
            f"{NOTE}. Sự kiện “{event['title']}”: tin nguồn cho thấy {main}. Kịch bản cơ sở giữ hướng này; "
            "nhánh ngược chiều và nhánh căng thẳng để đo rủi ro. Đây là phân tích thị trường, không phải khuyến nghị."
        ),
        "impacts": impacts,
        "scenarios": {
            "priced_in": "none",
            "branches": [
                {
                    "id": "base",
                    "name": "Cơ sở",
                    "probability": 0.55,
                    "regime": "normal",
                    "core_shocks": base,
                    "rationale": f"{NOTE}: diễn biến theo hướng tin nguồn ({main}).",
                    "source_ids": ids,
                },
                {
                    "id": "reverse",
                    "name": "Ngược chiều",
                    "probability": 0.25,
                    "regime": "normal",
                    "core_shocks": reverse,
                    "rationale": f"{NOTE}: thị trường phản ứng ngược với tin, mức nhỏ.",
                    "source_ids": ids,
                },
                {
                    "id": "stress",
                    "name": "Căng thẳng",
                    "probability": 0.20,
                    "regime": "stressed",
                    "core_shocks": stressed,
                    "rationale": f"{NOTE}: cú sốc lan sang VN-Index và tín dụng bất động sản như năm 2022.",
                    "source_ids": ids,
                },
            ],
        },
    }


def _adverse(factor: str) -> int:
    """The direction of a factor that lowers the value of the assets most exposed to it."""
    return 1 if factor in ("VN_RATE", "VN_GOV", "US10Y", "RE_SPREAD", "FIN_SPREAD", "DXY") else -1

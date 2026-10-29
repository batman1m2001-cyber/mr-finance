"""The lists an agent picks from (NEWS_EVIDENCE_BRD §4–§7): event types, target labels, channels, timeframes,
directions and what changes. Anything outside them sends the frame back (§9 rules 1 and 3)."""

from __future__ import annotations

import re
import time
import unicodedata
from datetime import date
from typing import Any, Dict, List, Optional

from procedural.goals import PURPOSES

# event type → its name; ``stat`` names the series its precedents are measured on (the statistics branch, §5)
EVENT_TYPES: Dict[str, Dict[str, str]] = {
    "second_property_tax": {"label": "Thuế với người sở hữu nhiều bất động sản"},
    "transfer_tax": {"label": "Thuế chuyển nhượng bất động sản"},
    "land_price_table": {"label": "Bảng giá đất"},
    "sector_policy": {"label": "Chính sách riêng một ngành"},
    "ownership_cap": {"label": "Giới hạn sở hữu cổ phần"},
    "bond_buyer_rule": {"label": "Điều kiện người mua trái phiếu doanh nghiệp"},
    "trading_tax": {"label": "Thuế giao dịch chứng khoán"},
    "market_upgrade": {"label": "Nâng hạng thị trường chứng khoán"},
    "gold_policy": {"label": "Chính sách vàng miếng"},
    "crypto_framework": {"label": "Khung pháp lý tài sản mã hóa"},
    "fx_transfer_rule": {"label": "Quy định ngoại hối, chuyển tiền"},
    "pit_relief": {"label": "Giảm trừ thuế thu nhập cá nhân"},
    "insurance_rule": {"label": "Quy định bảo hiểm liên kết đầu tư"},
    "global_min_tax": {"label": "Thuế tối thiểu toàn cầu"},
    "sbv_rate_hike": {"label": "NHNN tăng lãi suất điều hành"},
    "sbv_rate_cut": {"label": "NHNN giảm lãi suất điều hành"},
    "usd_vnd_rise": {"label": "Tỷ giá USD/VND tăng"},
    "metro_line": {"label": "Tuyến metro vận hành"},
    "airport": {"label": "Sân bay mới khai thác"},
    "ring_road": {"label": "Đường vành đai hoàn thành"},
    "outbound_transfer_control": {"label": "Kiểm soát chuyển tiền ra nước ngoài"},
    "fed_cut": {"label": "Fed giảm lãi suất", "stat": "VNINDEX"},
    "fed_hike": {"label": "Fed tăng lãi suất", "stat": "VNINDEX"},
    "new": {"label": "Loại mới"},  # always the qualitative branch (§4)
}

CHANNELS = ("lãi suất", "tín dụng", "tỷ giá", "thuế/phí", "pháp lý", "cung/cầu", "dòng vốn", "tâm lý thị trường")
CHANGES = ("giá", "dòng tiền", "chi phí", "thanh khoản", "thủ tục")
DIRECTIONS = {"positive": "Tích cực", "negative": "Tiêu cực", "unclear": "Chưa rõ"}
TIMEFRAMES = {"1w": "1 tuần", "1m": "1 tháng", "1-3m": "1–3 tháng", "3m": "3 tháng", ">3m": "trên 3 tháng"}

# the target labels (§7): ``kind:value``; a kind with a closed list names it, the rest take any non-empty value
ASSET_CLASSES = ("stock", "fund", "bond", "gold", "deposit", "cash", "real_estate", "business", "insurance", "crypto")
TARGETS: Dict[str, Optional[tuple]] = {
    "asset": ASSET_CLASSES,
    "sector": None,
    "ticker": None,
    "area": None,
    "loan": ("floating", "fx"),
    "plan": tuple(PURPOSES),
    "income": ("salary", "dividend", "rent"),
}
TARGET_KINDS = {"asset": "Tài sản", "sector": "Ngành", "ticker": "Mã", "area": "Khu vực BĐS", "loan": "Khoản vay",
                "plan": "Kế hoạch", "income": "Thu nhập"}  # fmt: skip
ASSET_NAMES = {"stock": "cổ phiếu", "fund": "chứng chỉ quỹ", "bond": "trái phiếu", "gold": "vàng", "deposit": "tiền gửi",
               "cash": "tiền mặt", "real_estate": "bất động sản", "business": "cổ phần tư nhân", "insurance": "bảo hiểm",
               "crypto": "tiền số"}  # fmt: skip
TARGET_VALUES = {"floating": "lãi thả nổi", "fx": "ngoại tệ", "salary": "lương", "dividend": "cổ tức", "rent": "tiền thuê",
                 **ASSET_NAMES, **PURPOSES}  # fmt: skip

# the series a type's precedents are measured on (P2, §5: any series the market store keeps, the CIO picks per type)
SERIES = {"VNINDEX": "VN-Index", "SJC": "Vàng SJC", "USDVND": "Tỷ giá USD/VND", "VN_GOV_10Y": "Lợi suất TPCP 10 năm"}
CIO_TYPES = ("_cio", "evidence_types")  # the CIO's additions (P2): new types and dates added to any type

MIN_PRECEDENTS = 8  # the statistics branch needs this many (Q1, the CIO's to settle)
MIN_EDGE = 0.10  # the same-direction share must beat the base rate by this much to call a direction (Q2)


def valid_target(label: str) -> bool:
    kind, _, value = str(label).partition(":")
    if kind not in TARGETS or not value:
        return False
    allowed = TARGETS[kind]
    return allowed is None or value in allowed


def target_label(label: str) -> str:
    """``plan:study_abroad`` → ``Kế hoạch: Du học``."""
    kind, _, value = label.partition(":")
    if kind == "area":
        from wealth import fixtures

        value = (fixtures.market().get("areas", {}).get(value) or {}).get("name", value)
    return f"{TARGET_KINDS.get(kind, kind)}: {TARGET_VALUES.get(value, value)}"


def _kept() -> Dict[str, Any]:
    from wealth import store

    got = store.result(*CIO_TYPES) or {}
    return {"types": dict(got.get("types") or {}), "dates": dict(got.get("dates") or {})}


def event_types() -> Dict[str, Dict[str, Any]]:
    """The catalogue an agent picks from: the built-in types, then the CIO's, with "Loại mới" last (P2)."""
    built = {k: v for k, v in EVENT_TYPES.items() if k != "new"}
    cio = {k: {"label": v["label"], "series": v.get("series") or [], "cio": True} for k, v in _kept()["types"].items()}
    return {**built, **cio, "new": EVENT_TYPES["new"]}


def events(seed: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Each type's precedent dates: ``seed`` (data/evidence.json) with the dates the CIO added, sorted, no repeats."""
    added = _kept()["dates"]
    return {k: sorted(set(seed.get(k, [])) | set(added.get(k, []))) for k in {*seed, *added}}


def slug(label: str) -> str:
    """``"Bầu cử Mỹ"`` → ``cio_bau_cu_my``: a CIO type's id, never one of the built-in ones."""
    plain = unicodedata.normalize("NFKD", label.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    return "cio_" + ("_".join(re.findall(r"[a-z0-9]+", plain.lower())) or "loai")[:40]


def save(event_type: Optional[str], label: Optional[str], dates: List[str], series: List[str], by: str) -> Dict[str, Any]:
    """The CIO adds a type (``label``) or dates to a type already there (``event_type``); dates are ISO days, none in
    the future. Returns {event_type, label, added}. Raises ValueError with the reason."""
    from wealth import store

    today = date.today().isoformat()
    good, bad = [], []
    for d in dates or []:
        d = str(d).strip()
        try:
            ok = date.fromisoformat(d).isoformat() == d and d <= today
        except ValueError:
            ok = False
        (good if ok else bad).append(d)
    if bad:
        raise ValueError(f"Ngày không hợp lệ (YYYY-MM-DD, không ở tương lai): {', '.join(bad[:5])}")
    off = [s for s in series or [] if s not in SERIES]
    if off:
        raise ValueError(f"Chuỗi không có: {', '.join(off)}")
    kept = _kept()
    if event_type:
        if event_type not in event_types() or event_type == "new":
            raise ValueError(f"Không có loại sự kiện {event_type!r}")
        et = event_type
    else:
        name = str(label or "").strip()
        if not name:
            raise ValueError("Cần tên loại sự kiện hoặc loại có sẵn")
        if any(v["label"].lower() == name.lower() for v in event_types().values()):
            raise ValueError(f"Đã có loại {name!r}")
        et = slug(name)
        kept["types"][et] = {"label": name[:80], "by": by, "at": time.time()}
    if et in kept["types"] and series:
        kept["types"][et]["series"] = list(dict.fromkeys(series))
    before = set(kept["dates"].get(et, []))
    kept["dates"][et] = sorted(before | set(good))
    store.put_result(*CIO_TYPES, kept)
    return {"event_type": et, "label": event_types()[et]["label"], "added": len(set(good) - before)}

"""The lists an agent picks from (NEWS_EVIDENCE_BRD §4–§7): event types, target labels, channels, timeframes,
directions and what changes. Anything outside them sends the frame back (§9 rules 1 and 3)."""

from __future__ import annotations

from typing import Dict, Optional

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

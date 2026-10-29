"""The trial's segments (B1.4): macro, policy and sector, from a news item's event type, else from the section of
the feed it came from (half of the news has no event type: its words matched none). Domestic or international is
the item's own ``kind``. The brokers' views are a fourth segment once the owner names their sources."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, Optional

SEGMENTS = {"macro": "Vĩ mô", "policy": "Chính sách", "sector": "Ngành, tài sản"}

OF_TYPE = {
    "monetary": "macro",
    "fx": "macro",
    "credit": "macro",
    "commodity": "macro",
    "geopolitics": "macro",
    "regulation": "policy",
    "equity": "sector",
    "real_estate": "sector",
    "gold": "sector",
    "crypto": "sector",
}

# a feed's section, for an item whose words named no event type (data/news_config.json sources)
OF_SOURCE = {
    "vnexpress_tg": "macro",
    "vneconomy_tg": "macro",
    "vneconomy_tc": "macro",
    "vietstock_vm": "macro",
    "fed": "macro",
    "ecb": "macro",
    "vneconomy_ck": "sector",
    "vietstock_cp": "sector",
    "cafef_ck": "sector",
    "vneconomy_do": "sector",
    "vnexpress_kd": "sector",
}

REGIONS = {"domestic": "Trong nước", "intl": "Quốc tế"}

# the business's four groups (AGENT_EVALUATION_PLAN §2.1): a news item's, and an engine factor's
FAMILIES = {
    "real_estate": "Bất động sản",
    "stocks": "Chứng khoán",
    "policy_macro": "Chính sách, vĩ mô",
    "other": "Khác",
}
FAMILY_OF_TYPE = {
    "real_estate": "real_estate",
    "equity": "stocks",
    "monetary": "policy_macro",
    "fx": "policy_macro",
    "credit": "policy_macro",
    "commodity": "policy_macro",
    "geopolitics": "policy_macro",
    "regulation": "policy_macro",
    "gold": "other",
    "crypto": "other",
}
FAMILY_OF_SOURCE = {  # the section, for an item whose words named no event type; vnexpress_kd is mixed: none
    "vneconomy_do": "real_estate",
    "vneconomy_ck": "stocks",
    "vietstock_cp": "stocks",
    "cafef_ck": "stocks",
    "vnexpress_tg": "policy_macro",
    "vneconomy_tg": "policy_macro",
    "vneconomy_tc": "policy_macro",
    "vietstock_vm": "policy_macro",
    "fed": "policy_macro",
    "ecb": "policy_macro",
}
FAMILY_OF_FACTOR = {
    "VN_HOUSE": "real_estate",
    "RE_SPREAD": "real_estate",
    "VNINDEX": "stocks",
    "GLOBAL_EQ": "stocks",
    "FOREIGN_FLOW": "stocks",
    "FIN_SPREAD": "stocks",
    "VN_RATE": "policy_macro",
    "VN_GOV": "policy_macro",
    "USDVND": "policy_macro",
    "US10Y": "policy_macro",
    "DXY": "policy_macro",
    "GOLD": "other",
    "BTC": "other",
    "BRENT": "other",
    "SJC_GAP": "other",
}


def family_of_item(item: Dict[str, Any]) -> Optional[str]:
    """real_estate, stocks, policy_macro or other; None when neither its words nor its section say."""
    return FAMILY_OF_TYPE.get(item.get("event_type") or "") or FAMILY_OF_SOURCE.get(item.get("source") or "")


def family_of_factor(factor: str) -> str:
    return FAMILY_OF_FACTOR.get(factor, "other")


def of_item(item: Dict[str, Any]) -> Optional[str]:
    return OF_TYPE.get(item.get("event_type") or "") or OF_SOURCE.get(item.get("source") or "")


def of_items(items: Iterable[Dict[str, Any]]) -> Optional[str]:
    """An event's segment when the agent named none that is known: its news's most common one."""
    got = Counter(s for s in map(of_item, items) if s)
    return got.most_common(1)[0][0] if got else None


def region(items: Iterable[Dict[str, Any]]) -> Optional[str]:
    got = Counter(i.get("kind") for i in items if i.get("kind") in REGIONS)
    return got.most_common(1)[0][0] if got else None

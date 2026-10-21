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


def of_item(item: Dict[str, Any]) -> Optional[str]:
    return OF_TYPE.get(item.get("event_type") or "") or OF_SOURCE.get(item.get("source") or "")


def of_items(items: Iterable[Dict[str, Any]]) -> Optional[str]:
    """An event's segment when the agent named none that is known: its news's most common one."""
    got = Counter(s for s in map(of_item, items) if s)
    return got.most_common(1)[0][0] if got else None


def region(items: Iterable[Dict[str, Any]]) -> Optional[str]:
    got = Counter(i.get("kind") for i in items if i.get("kind") in REGIONS)
    return got.most_common(1)[0][0] if got else None

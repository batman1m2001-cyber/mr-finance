"""Write data/news_config.json: where news comes from and how it is sorted (BRD FR-101…105).

- ``sources``: the white list (BR-02). Public RSS feeds only, each checked to answer with items on
  2026-10-15. Báo Đầu tư, Nhân Dân and VTV are in the BRD's list but their feeds returned no items
  or 404 that day; they stay out until a working URL is found.
- ``keywords``: which factor of the engine's model a headline touches (relevance), which event
  type it hints at, and which words make a domestic outlet's story international (FR-102).
- ``restricted``: the restricted list (BR-04). A MOCK list for the demo — invented names only.
  The bank's real list never goes in this public repository.
- ``gates``: a published time more than ``future_minutes`` after ingestion is refused (BRD F20);
  items older than ``max_age_days`` are not ingested.

    uv run python scripts/make_news_config.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "news_config.json"

SOURCES = [
    # id, outlet, section, url, kind
    ("vnexpress_kd", "VnExpress", "Kinh doanh", "https://vnexpress.net/rss/kinh-doanh.rss", "domestic"),
    ("vnexpress_tg", "VnExpress", "Thế giới", "https://vnexpress.net/rss/the-gioi.rss", "intl"),
    ("vneconomy_tg", "VnEconomy", "Kinh tế thế giới", "https://vneconomy.vn/kinh-te-the-gioi.rss", "intl"),
    ("vneconomy_tc", "VnEconomy", "Tài chính", "https://vneconomy.vn/tai-chinh.rss", "domestic"),
    ("vneconomy_ck", "VnEconomy", "Chứng khoán", "https://vneconomy.vn/chung-khoan.rss", "domestic"),
    ("vneconomy_do", "VnEconomy", "Địa ốc", "https://vneconomy.vn/dia-oc.rss", "domestic"),
    ("vietstock_vm", "Vietstock", "Vĩ mô", "https://vietstock.vn/761/kinh-te/vi-mo.rss", "domestic"),
    ("vietstock_cp", "Vietstock", "Cổ phiếu", "https://vietstock.vn/830/chung-khoan/co-phieu.rss", "domestic"),
    ("cafef_ck", "CafeF", "Thị trường chứng khoán", "https://cafef.vn/thi-truong-chung-khoan.rss", "domestic"),
    ("fed", "Federal Reserve", "Press releases", "https://www.federalreserve.gov/feeds/press_all.xml", "intl"),
    ("ecb", "European Central Bank", "Press", "https://www.ecb.europa.eu/rss/press.html", "intl"),
]

# engine factor → words in a headline or summary (lower case; matched as whole words)
FACTOR_WORDS = {
    "US10Y": ["lợi suất trái phiếu mỹ", "trái phiếu kho bạc", "treasury", "lợi suất mỹ", "fed", "fomc"],
    "DXY": ["đồng usd", "chỉ số usd", "dxy", "đồng bạc xanh", "dollar"],
    "GLOBAL_EQ": ["phố wall", "s&p 500", "nasdaq", "dow jones", "chứng khoán mỹ", "chứng khoán châu á", "wall street"],
    "BRENT": ["giá dầu", "dầu brent", "opec", "dầu thô", "oil"],
    "GOLD": ["giá vàng", "vàng thế giới", "gold"],
    "BTC": ["bitcoin", "tiền số", "tiền mã hóa", "crypto"],
    "USDVND": ["tỷ giá", "usd/vnd", "tiền đồng", "ngoại tệ"],
    "VN_RATE": [
        "lãi suất điều hành",
        "nhnn",
        "ngân hàng nhà nước",
        "lãi suất liên ngân hàng",
        "lãi suất huy động",
        "lãi suất cho vay",
        "lãi suất",
    ],
    "VN_GOV": ["trái phiếu chính phủ", "tpcp", "kho bạc nhà nước"],
    "RE_SPREAD": ["trái phiếu doanh nghiệp bất động sản", "nợ xấu bất động sản", "đáo hạn trái phiếu"],
    "FIN_SPREAD": ["ngân hàng", "nợ xấu", "tín dụng", "trái phiếu doanh nghiệp"],
    "VNINDEX": ["vn-index", "vnindex", "chứng khoán", "cổ phiếu", "hose", "thị trường chứng khoán"],
    "FOREIGN_FLOW": ["khối ngoại", "nhà đầu tư nước ngoài", "nâng hạng", "bán ròng", "mua ròng"],
    "SJC_GAP": ["vàng miếng", "sjc", "chênh lệch giá vàng"],
    "VN_HOUSE": ["bất động sản", "nhà ở", "căn hộ", "địa ốc", "giá nhà", "chung cư"],
}

EVENT_TYPES = [  # first match wins, in this order
    (
        "monetary",
        "Chính sách tiền tệ",
        ["lãi suất", "fed", "fomc", "nhnn", "ngân hàng nhà nước", "ecb", "monetary policy"],
    ),
    ("fx", "Tỷ giá", ["tỷ giá", "usd/vnd", "đồng usd", "ngoại tệ"]),
    ("gold", "Vàng", ["giá vàng", "vàng miếng", "vàng thế giới", "gold", "sjc"]),
    ("credit", "Tín dụng, trái phiếu", ["trái phiếu", "tín dụng", "nợ xấu"]),
    ("real_estate", "Bất động sản", ["bất động sản", "nhà ở", "căn hộ", "địa ốc", "chung cư"]),
    ("regulation", "Chính sách, quy định", ["nghị định", "thông tư", "luật", "dự thảo", "thuế", "quyết định"]),
    ("commodity", "Hàng hóa", ["giá dầu", "opec", "dầu thô", "giá bạc", "hàng hóa"]),
    ("crypto", "Tiền số", ["bitcoin", "tiền số", "tiền mã hóa"]),
    ("equity", "Thị trường cổ phiếu", ["chứng khoán", "cổ phiếu", "vn-index", "khối ngoại", "nâng hạng"]),
    ("geopolitics", "Địa chính trị, thương mại", ["thuế quan", "chiến tranh", "trừng phạt", "xung đột", "tariff"]),
]

INTL_WORDS = [
    "mỹ",
    "fed",
    "trung quốc",
    "châu âu",
    "ecb",
    "nhật bản",
    "imf",
    "opec",
    "thế giới",
    "toàn cầu",
    "phố wall",
    "anh quốc",
    "hàn quốc",
    "ấn độ",
]
DOMESTIC_WORDS = ["việt nam", "nhnn", "vn-index", "tp hcm", "tp.hcm", "hà nội", "hose", "trong nước", "sjc"]

# A MOCK restricted list: invented names (none is a real company), so the hold can be shown and tested.
RESTRICTED = [
    {"name": "Sao Mai Land (mock)", "aliases": ["sao mai land", "bđs sao mai"], "ticker": "SML"},
    {"name": "Hòa Bình Energy (mock)", "aliases": ["hòa bình energy", "năng lượng hòa bình"], "ticker": "HBE"},
    {"name": "Kim Phát Holdings (mock)", "aliases": ["kim phát holdings"], "ticker": "KPH"},
]

CONFIG = {
    "version": "NEWS-DEMO-2026-10",
    "note": "Danh sách nguồn công khai và từ khóa cho demo; danh sách hạn chế là giả lập (tên tự đặt).",
    "gates": {"future_minutes": 10, "max_age_days": 7, "fetch_timeout_s": 15},
    "sources": [
        {"id": i, "outlet": o, "section": s, "url": u, "kind": k, "approved": True} for i, o, s, u, k in SOURCES
    ],
    "factor_words": FACTOR_WORDS,
    "event_types": [{"id": i, "label": label, "words": w} for i, label, w in EVENT_TYPES],
    "intl_words": INTL_WORDS,
    "domestic_words": DOMESTIC_WORDS,
    "restricted": RESTRICTED,
}


def main() -> None:
    OUT.write_text(json.dumps(CONFIG, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

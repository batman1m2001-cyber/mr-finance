"""What a client says, read without a model: the sentences the demo needs, in Vietnamese.

    "Tôi có 1 căn ở Thảo Điền mua 2019 giá 8 tỷ"      → a property (area, year, price)
    "Nhà tôi có 10 lượng vàng"                          → gold
    "Tôi có 2 con, 14 tuổi và 10 tuổi"                  → two dependents
    "Tôi cho thuê căn hộ được 15 triệu/tháng"           → income
    "Tôi đang nợ 500 triệu, trả 12 triệu mỗi tháng"     → a loan
    "Tôi có 20% cổ phần công ty X trị giá 5 tỷ"         → business shares

Each match is a record the tools would have written (declare/tools.py writes the same shapes).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from wealth.text import ascii_lower

TY, TR = 1_000_000_000, 1_000_000
YEAR = 2026

AREAS = {
    "thao_dien": ("thao dien",),
    "phu_my_hung": ("phu my hung", "quan 7", "q7"),
    "vinhomes_grand_park": ("vinhomes grand park", "grand park", "quan 9", "q9"),
    "quan_3": ("quan 3", "q3", "vo van tan"),
    "long_thanh": ("long thanh",),
}


def area_of(text: str) -> Optional[str]:
    low = ascii_lower(text)
    for key, names in AREAS.items():
        if any(re.search(rf"\b{re.escape(n)}\b", low) for n in names):
            return key
    return None


def money(text: str) -> List[float]:
    """Every amount in a sentence, in VND: ``8 tỷ``, ``1,5 tỷ``, ``850 triệu``, ``120tr``."""
    out = []
    for num, unit in re.findall(r"(\d+(?:[.,]\d+)?)\s*(ty|trieu|tr)\b", ascii_lower(text)):
        v = float(num.replace(",", "."))
        out.append(v * (TY if unit == "ty" else TR))
    return out


def parse(message: str) -> List[Dict[str, Any]]:
    """The records in one message: ``{"kind": "asset" | "dependent" | "income", "data": {...}}``."""
    low = ascii_lower(message)
    out: List[Dict[str, Any]] = []
    amounts = money(message)

    # a property: "căn", "nhà", "đất", "biệt thự", "căn hộ" with a place or a price
    if re.search(r"\b(can ho|can|nha|dat|biet thu|chung cu)\b", low) and not re.search(r"\bthue nha\b", low):
        area = area_of(message)
        year = re.search(r"\b(19[89]\d|20[0-2]\d)\b", low)
        sqm = re.search(r"(\d+(?:[.,]\d+)?)\s*m2", low)
        price = amounts[0] if amounts and "cho thue" not in low else None
        if area or price:
            kind = "Đất" if re.search(r"\bdat\b", low) else "Nhà" if re.search(r"\bnha\b", low) else "Căn hộ"
            place = {
                "thao_dien": "Thảo Điền",
                "phu_my_hung": "Phú Mỹ Hưng",
                "vinhomes_grand_park": "Vinhomes Grand Park",
                "quan_3": "Quận 3",
                "long_thanh": "Long Thành",
            }.get(area or "", "")
            out.append(
                {
                    "kind": "asset",
                    "data": {
                        "class": "real_estate",
                        "name": f"{kind} {place}".strip() + " (tự khai)",
                        "area": area,
                        "sqm": float(sqm.group(1).replace(",", ".")) if sqm else None,
                        "purchase_year": int(year.group(1)) if year else None,
                        "purchase_price": price,
                        # without a size we value it at what the client paid (or says it is worth)
                        "value": price if not sqm else None,
                    },
                }
            )

    gold = re.search(r"(\d+(?:[.,]\d+)?)\s*(luong|cay)\s*(vang)?", low)
    if gold and ("vang" in low):
        out.append(
            {
                "kind": "asset",
                "data": {
                    "class": "gold",
                    "name": "Vàng (tự khai)",
                    "qty": float(gold.group(1).replace(",", ".")),
                },
            }
        )

    kids = re.search(r"(\d+)\s*(con|chau)\b", low)
    ages = [int(a) for a in re.findall(r"(\d{1,2})\s*tuoi", low)]
    if kids or ages:
        n = int(kids.group(1)) if kids else len(ages)
        for i in range(max(n, len(ages))):
            age = ages[i] if i < len(ages) else None
            out.append(
                {
                    "kind": "dependent",
                    "data": {
                        "name": f"Con {i + 1}",
                        "relation": "Con",
                        "birth_year": YEAR - age if age is not None else None,
                    },
                }
            )

    if re.search(r"(cho thue|thu nhap|luong).*(thang)", low) and amounts:
        label = "Tiền cho thuê" if "cho thue" in low else "Thu nhập thêm"
        out.append({"kind": "income", "data": {"label": label + " (tự khai)", "amount": amounts[-1]}})

    if re.search(r"\b(no|vay)\b", low) and amounts and not re.search(r"cho vay", low):
        monthly = amounts[1] if len(amounts) > 1 and "thang" in low else 0
        out.append(
            {
                "kind": "asset",
                "data": {
                    "class": "loan",
                    "name": "Khoản nợ (tự khai)",
                    "value": amounts[0],
                    "monthly_payment": monthly,
                    "rate_type": "fixed",
                },
            }
        )

    if "co phan" in low and amounts:
        share = re.search(r"(\d+(?:[.,]\d+)?)\s*%", low)
        company = re.search(r"cong ty\s+([\w\s]+?)(?:\s+(?:tri gia|gia tri|khoang)|$)", low)
        out.append(
            {
                "kind": "asset",
                "data": {
                    "class": "business",
                    "value": amounts[-1],
                    "name": (f"{share.group(1)}% cổ phần " if share else "Cổ phần ")
                    + (company.group(1).strip().title() if company else "doanh nghiệp")
                    + " (tự khai)",
                },
            }
        )
    return out

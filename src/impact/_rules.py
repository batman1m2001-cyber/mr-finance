"""Each factor's rule: which holdings it touches, and how much before its probability.

A rule returns hits ``{"exposure", "sensitivity", "raw", "affected", "message"}``: ``exposure`` is
what the client holds in harm's way (VND), ``sensitivity`` how much of it moves, ``raw`` the move
in VND (negative: a loss; for a yearly cost, one year of it), ``message`` the line the client reads.
The alert's impact is ``raw × probability``.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List

from wealth.money import vnd

Hit = Dict[str, Any]
H = List[Dict[str, Any]]


def _assets(holdings: H, cls: str) -> H:
    return [h for h in holdings if h["kind"] == "asset" and h["class"] == cls]


def second_property(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    homes = sorted(_assets(hs, "real_estate"), key=lambda h: -h["value"])
    if len(homes) < 2:
        return []
    # the home lived in is spared; the others are taxed (the largest one lived in, else the largest)
    lived = next((h for h in homes if h["detail"].get("use") == "Ở"), homes[0])
    others = [h for h in homes if h is not lived]
    exposure = sum(h["value"] for h in others)
    rate = f["rule"]["annual_rate"]
    top = others[0]
    return [
        {
            "exposure": exposure,
            "sensitivity": -rate,
            "raw": -exposure * rate,
            "affected": [h["name"] for h in others],
            "message": f"Ước tính thuế phải nộp tăng thêm {vnd(exposure * rate)}/năm cho {len(others)} BĐS ngoài nhà ở chính "
            f"(lớn nhất: {top['name']}).",
        }
    ]


def transfer_tax(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    out = []
    for h in _assets(hs, "real_estate"):
        if h["detail"].get("use") not in ("Cho thuê", "Đầu tư") or not h.get("cost"):
            continue
        old = h["value"] * f["rule"]["old_rate"]
        new = max(0.0, h["value"] - h["cost"]) * f["rule"]["gain_rate"]
        diff = old - new  # positive: the new way is cheaper
        out.append(
            {
                "exposure": h["value"],
                "sensitivity": diff / h["value"],
                "raw": diff,
                "affected": [h["name"]],
                "message": f"Nếu bán {h['name']}: thuế cũ {vnd(old)}, cách tính mới {vnd(new)} — "
                + ("tiết kiệm " if diff > 0 else "tốn thêm ")
                + f"{vnd(abs(diff))}. "
                "Thời điểm bán trước hay sau khi luật có hiệu lực tạo ra chênh lệch này.",
            }
        )
    return out


def land_fees(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    land = [h for h in _assets(hs, "real_estate") if "đất" in (h["detail"].get("property_type") or h["name"]).lower()]
    if not land:
        return []
    exposure = sum(h["value"] for h in land)
    rate = f["rule"]["rate"]
    return [
        {
            "exposure": exposure,
            "sensitivity": -rate,
            "raw": -exposure * rate,
            "affected": [h["name"] for h in land],
            "message": f"Bảng giá đất mới làm tăng lệ phí trước bạ, thuế và tiền sử dụng đất khi chuyển nhượng: "
            f"ước tính thêm {vnd(exposure * rate)} cho {', '.join(h['name'] for h in land)}.",
        }
    ]


def sector(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = [
        h
        for h in hs
        if h["kind"] == "asset" and h["class"] in ("stock", "bond") and h["detail"].get("sector") == f["rule"]["sector"]
    ]
    if not rows:
        return []
    s = f["rule"]["sensitivity"]
    # a stock moves with its beta, a bond less (its coupon still comes)
    weight = lambda h: (h["detail"].get("beta") or 1.0) if h["class"] == "stock" else 0.3  # noqa: E731
    raw = sum(h["value"] * s * weight(h) for h in rows)
    exposure = sum(h["value"] for h in rows)
    return [
        {
            "exposure": exposure,
            "sensitivity": raw / exposure,
            "raw": raw,
            "affected": [h["name"] for h in rows],
            "message": f"Nắm giữ {vnd(exposure)} cổ phiếu, trái phiếu ngành {f['rule']['sector']}: tác động lan sang cả ngành, "
            f"ước tính {vnd(raw, signed=True)}.",
        }
    ]


def issuer_concentration(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = [
        h
        for h in _assets(hs, "stock")
        if h["detail"].get("sector") == f["rule"]["sector"] and h["value"] >= f["rule"]["min_value"]
    ]
    if not rows:
        return []
    exposure = sum(h["value"] for h in rows)
    s = f["rule"]["sensitivity"]
    names = ", ".join(f"{h['detail'].get('ticker')} ({vnd(h['value'])})" for h in rows)
    return [
        {
            "exposure": exposure,
            "sensitivity": s,
            "raw": exposure * s,
            "affected": [h["name"] for h in rows],
            "message": f"Cổ phiếu ngân hàng nắm giữ lớn: {names}. Cổ đông lớn buộc thoái vốn có thể gây áp lực bán, "
            f"ước tính {vnd(exposure * s, signed=True)}.",
        }
    ]


def bond_kind(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = [h for h in _assets(hs, "bond") if h["detail"].get("bond_kind") == f["rule"]["bond_kind"]]
    if not rows:
        return []
    exposure = sum(h["value"] for h in rows)
    s = f["rule"]["sensitivity"]
    return [
        {
            "exposure": exposure,
            "sensitivity": s,
            "raw": exposure * s,
            "affected": [h["name"] for h in rows],
            "message": f"{vnd(exposure)} trái phiếu doanh nghiệp: có thể không mua thêm được, thanh khoản thứ cấp giảm "
            f"(chiết khấu khi cần bán ước tính {vnd(exposure * s, signed=True)}).",
        }
    ]


def trading_cost(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    stocks = sum(h["value"] for h in _assets(hs, "stock"))
    if stocks <= 0:
        return []
    cost = stocks * f["rule"]["turnover"] * f["rule"]["rate"]
    return [
        {
            "exposure": stocks,
            "sensitivity": -cost / stocks,
            "raw": -cost,
            "affected": ["Danh mục cổ phiếu"],
            "message": f"Với mức giao dịch khoảng {f['rule']['turnover']:g} lần danh mục mỗi năm, chi phí thuế tăng "
            f"ước tính {vnd(cost)}/năm.",
        }
    ]


def large_caps(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = [h for h in _assets(hs, "stock") if h["detail"].get("ticker") in f["rule"]["tickers"]]
    if not rows:
        return []
    exposure = sum(h["value"] for h in rows)
    s = f["rule"]["sensitivity"]
    names = ", ".join(sorted({h["detail"]["ticker"] for h in rows}))
    return [
        {
            "exposure": exposure,
            "sensitivity": s,
            "raw": exposure * s,
            "affected": [h["name"] for h in rows],
            "message": f"Cơ hội: dòng vốn ngoại vào nhóm vốn hóa lớn ({names}); {vnd(exposure)} đang nắm giữ, "
            f"ước tính {vnd(exposure * s, signed=True)}.",
        }
    ]


def gold(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = _assets(hs, "gold")
    if not rows:
        return []
    exposure = sum(h["value"] for h in rows)
    s = -mk["gold"]["world_gap"] / 2  # half of today's gap to the world price closes
    return [
        {
            "exposure": exposure,
            "sensitivity": s,
            "raw": exposure * s,
            "affected": [h["name"] for h in rows],
            "message": f"Chênh lệch giá vàng trong nước và thế giới ({mk['gold']['world_gap']:.0%}) thu hẹp: giá trị vàng đang giữ "
            f"ước tính {vnd(exposure * s, signed=True)}.",
        }
    ]


def crypto(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = _assets(hs, "crypto")
    if not rows:
        return []
    exposure = sum(h["value"] for h in rows)
    s = f["rule"]["sensitivity"]
    return [
        {
            "exposure": exposure,
            "sensitivity": s,
            "raw": exposure * s,
            "affected": [h["name"] for h in rows],
            "message": f"Khung pháp lý mới mở kênh đầu tư hợp pháp cho {vnd(exposure)} tài sản số đang tự khai; "
            f"có thể chuyển sang sàn được cấp phép.",
        }
    ]


def study_abroad(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    events = [
        e
        for e in profile.get("events", [])
        if e.get("direction") == "out"
        and ("du học" in e["label"].lower() or "(mỹ)" in e["label"].lower() or "(úc)" in e["label"].lower())
    ]
    if not events:
        return []
    exposure = sum(e["amount"] for e in events)
    move = f["rule"]["fx_move"]
    return [
        {
            "exposure": exposure,
            "sensitivity": -move,
            "raw": -exposure * move,
            "affected": [e["label"] for e in events],
            "message": f"Khoản chi bằng ngoại tệ sắp tới ({', '.join(e['label'] for e in events)}): tỷ giá +{move:.0%} làm tăng "
            f"thêm {vnd(exposure * move)}. Có thể chuẩn bị ngoại tệ từ sớm.",
        }
    ]


def pit_relief(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    income = profile.get("income_monthly", 0)
    if income < 30_000_000:
        return []
    deps = len(profile.get("dependents", []))
    r = f["rule"]
    yearly = 12 * (r["self"] + deps * r["dependent"]) * r["marginal"]
    return [
        {
            "exposure": income * 12,
            "sensitivity": yearly / (income * 12),
            "raw": yearly,
            "affected": ["Thu nhập từ lương"],
            "message": f"Giảm trừ gia cảnh tăng ({'bản thân' + (f' và {deps} người phụ thuộc' if deps else '')}): "
            f"thu nhập thực nhận tăng khoảng "
            f"{vnd(yearly / 12)}/tháng.",
        }
    ]


def insurance(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = [h for h in _assets(hs, "insurance") if h["value"] > 0]
    if not rows:
        return []
    exposure = sum(h["value"] for h in rows)
    s = f["rule"]["sensitivity"]
    return [
        {
            "exposure": exposure,
            "sensitivity": s,
            "raw": exposure * s,
            "affected": [h["name"] for h in rows],
            "message": f"Quyền lợi và phí hủy hợp đồng bảo hiểm liên kết đầu tư thay đổi: nếu hủy, ước tính "
            f"{vnd(exposure * s, signed=True)}.",
        }
    ]


def business(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = _assets(hs, "business")
    if not rows:
        return []
    exposure = sum(h["value"] for h in rows)
    s = f["rule"]["sensitivity"]
    return [
        {
            "exposure": exposure,
            "sensitivity": s,
            "raw": exposure * s,
            "affected": [h["name"] for h in rows],
            "message": f"Lợi nhuận doanh nghiệp giảm do thuế và ưu đãi thay đổi: giá trị cổ phần ước tính "
            f"{vnd(exposure * s, signed=True)}.",
        }
    ]


def rates(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    move = f["rule"]["move"]
    out = []
    loans = [h for h in hs if h["kind"] == "liability" and h["detail"].get("rate_type") == "floating"]
    if loans:
        owed = sum(h["value"] for h in loans)
        out.append(
            {
                "exposure": owed,
                "sensitivity": -move,
                "raw": -owed * move,
                "affected": [h["name"] for h in loans],
                "message": f"Khoản vay lãi thả nổi {vnd(owed)}: chi phí lãi tăng {vnd(owed * move)}/năm "
                f"(khoảng {vnd(owed * move / 12)}/tháng).",
            }
        )
    bonds = _assets(hs, "bond")
    if bonds:
        exposure = sum(h["value"] for h in bonds)
        raw = -sum(h["value"] * (h["detail"].get("duration") or 1) * move for h in bonds)
        out.append(
            {
                "exposure": exposure,
                "sensitivity": raw / exposure,
                "raw": raw,
                "affected": [h["name"] for h in bonds],
                "message": f"Giá trái phiếu giảm theo thời gian đáo hạn bình quân: {vnd(raw, signed=True)} trên {vnd(exposure)}.",
            }
        )
    return out


def area(f: Dict, hs: H, profile: Dict, mk: Dict) -> List[Hit]:
    rows = [h for h in _assets(hs, "real_estate") if h["detail"].get("area") == f["rule"]["area"]]
    if not rows:
        return []
    exposure = sum(h["value"] for h in rows)
    s = f["rule"]["sensitivity"]
    return [
        {
            "exposure": exposure,
            "sensitivity": s,
            "raw": exposure * s,
            "affected": [h["name"] for h in rows],
            "message": f"Cơ hội: BĐS gần dự án ({', '.join(h['name'] for h in rows)}) ước tính {vnd(exposure * s, signed=True)}.",
        }
    ]


RULES: Dict[str, Callable[..., List[Hit]]] = {
    "second_property": second_property,
    "transfer_tax": transfer_tax,
    "land_fees": land_fees,
    "sector": sector,
    "issuer_concentration": issuer_concentration,
    "bond_kind": bond_kind,
    "trading_cost": trading_cost,
    "large_caps": large_caps,
    "gold": gold,
    "crypto": crypto,
    "study_abroad": study_abroad,
    "pit_relief": pit_relief,
    "insurance": insurance,
    "business": business,
    "rates": rates,
    "area": area,
}


def severity(pct_of_net_worth: float) -> str:
    """🔴 high from 1% of net worth, 🟡 medium from 0.3%, 🟢 low below."""
    a = abs(pct_of_net_worth)
    return "high" if a >= 0.01 else "medium" if a >= 0.003 else "low"

"""Each holding → how its value moves with the factors (BRD 9.3).

A holding's ``loads`` maps a factor to the share of the holding's value that one unit of the
factor's move changes (a 1 % VN-Index move on a beta-1.15 stock: 0.0115). Assets count positive,
liabilities negative (``sign``): a USD loan's debt grows with USD/VND, which lowers net worth.
A floating VND loan's load is the extra interest over the horizon, so it depends on the horizon.

Proxies the BRD calls "theo mô hình" (real estate, private equity) and our own stand-ins are
flagged ``modelled`` with the reason in ``method``; holdings no factor moves (cash, deposits,
insurance, card debt) get no loads and say so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from engine.model import FactorModel

# one unit of a factor's move as a share of value: 1 % = 0.01, 1 bp = 0.0001, 1 pp = 0.01
_UNIT = {"pct": 0.01, "bp": 0.0001, "pp": 0.01, "sd": 0.0}

_FINANCIAL_SECTORS = {"Ngân hàng", "Tài chính", "Chứng khoán", "Bảo hiểm"}


@dataclass
class Exposure:
    key: str
    owner: str
    cls: str
    name: str
    value: float  # VND, positive
    sign: int  # +1 asset, −1 liability
    loads: Dict[str, float] = field(default_factory=dict)  # factor → share of value per unit move
    idio_var_month: float = 0.0  # stock-specific variance per month, as a share of value squared
    modelled: bool = False
    method: str = ""


def exposures(holdings: List[Dict[str, Any]], model: FactorModel, months: float) -> List[Exposure]:
    """The exposures of every holding for a horizon of ``months``."""
    return [exposure(h, model, months) for h in holdings if h.get("value")]


def exposure(h: Dict[str, Any], model: FactorModel, months: float) -> Exposure:
    cls = h["class"]
    d = h.get("detail") or {}
    sign = -1 if h.get("kind") == "liability" else 1
    e = Exposure(key=h["key"], owner=h.get("owner", ""), cls=cls, name=h["name"], value=float(h["value"]), sign=sign)
    lo = model.loadings

    def load(factor: str, per_unit: float) -> None:
        e.loads[factor] = e.loads.get(factor, 0.0) + per_unit * _UNIT[model.factor(factor).unit]

    if cls == "stock":
        beta = float(d.get("beta") or 1.0)
        if (d.get("currency") or "VND") != "VND":
            load("GLOBAL_EQ", beta)
            load("USDVND", 1.0)
            e.method = f"Cổ phiếu nước ngoài: beta {beta:g} theo cổ phiếu toàn cầu, quy đổi VND"
        else:
            load("VNINDEX", beta)
            usd = float(lo.get("usd_revenue", {}).get(d.get("ticker"), 0.0))
            if usd:
                load("USDVND", usd)
            r2 = float(d.get("r2") or lo.get("stock_r2", 0.35))
            vn = model.factor("VNINDEX").vol_month * _UNIT["pct"]
            e.idio_var_month = (beta * vn) ** 2 * (1.0 - r2) / r2
            e.method = f"Beta {beta:g} theo VN-Index" + (f", {usd:.0%} doanh thu USD theo tỷ giá" if usd else "")
            e.method += f"; rủi ro riêng theo R² {r2:g} (giả định)"
    elif cls == "bond":
        dur = float(d.get("duration") or 0.0)
        mod = dur / (1.0 + float(d.get("coupon") or 0.0))
        load("VN_GOV", -mod)
        kind, sector = d.get("bond_kind"), d.get("sector")
        if kind == "government":
            e.method = f"Duration điều chỉnh {mod:.2f} theo lợi suất TPCP"
        elif kind == "bank" or sector in _FINANCIAL_SECTORS:
            load("FIN_SPREAD", -mod)
            e.method = f"Duration điều chỉnh {mod:.2f} theo lợi suất TPCP và chênh lệch tín dụng DN tài chính"
        elif sector == "Bất động sản":
            load("RE_SPREAD", -mod)
            e.method = f"Duration điều chỉnh {mod:.2f} theo lợi suất TPCP và chênh lệch tín dụng DN bất động sản"
        else:
            e.modelled = True
            e.method = (
                f"Duration điều chỉnh {mod:.2f} theo lợi suất TPCP; mô hình chưa có yếu tố chênh lệch tín dụng "
                f"cho ngành {sector or 'này'}"
            )
    elif cls == "fund":
        ft = d.get("fund_type") or ""
        if ft == "equity":
            beta = float(lo.get("fund_beta", {}).get("equity", 1.0))
            load("VNINDEX", beta)
            e.method = f"Quỹ cổ phiếu: beta {beta:g} theo VN-Index (giả định)"
        elif ft in lo.get("fund_duration", {}) and lo["fund_duration"][ft]:
            dur = float(lo["fund_duration"][ft])
            load("VN_GOV", -dur)
            e.method = f"Quỹ trái phiếu: duration {dur:g} theo lợi suất TPCP"
        else:
            e.method = "Quỹ tiền tệ: không chịu tác động giá đáng kể"
    elif cls == "gold":
        gap = float(lo.get("gold_sjc_gap", 0.9))
        load("GOLD", 1.0)
        load("USDVND", 1.0)
        load("SJC_GAP", gap)
        e.method = f"Vàng thế giới + tỷ giá + {gap:g} × chênh lệch SJC"
    elif cls == "crypto":
        load("BTC", 1.0)
        load("USDVND", 1.0)
        sym = d.get("symbol") or "BTC"
        if sym != "BTC":
            e.modelled = True
            e.method = f"{sym}: dùng Bitcoin làm đại diện (giả định), quy đổi VND"
        else:
            e.method = "Bitcoin, quy đổi VND"
    elif cls == "fx":
        load("USDVND", 1.0)
        e.method = "Ngoại tệ quy đổi VND"
    elif cls == "real_estate":
        load("VN_HOUSE", 1.0)
        e.modelled = True
        e.method = "Bất động sản: đại diện bằng giá nhà ở Việt Nam (theo mô hình)"
    elif cls == "business":
        k = float(lo.get("private_equity_vnindex", 0.5))
        load("VNINDEX", k)
        e.modelled = True
        e.method = f"Cổ phần tư nhân: {k:g} × VN-Index (theo mô hình)"
    elif cls == "loan":
        if (d.get("currency") or "VND") != "VND":
            load("USDVND", 1.0)
            e.method = "Khoản vay ngoại tệ: tỷ giá tăng thì nợ tăng"
        elif d.get("rate_type") == "floating":
            load("VN_RATE", months / 12.0)
            e.method = f"Vay VND thả nổi: chi phí lãi tăng thêm trong {_months_label(months)}"
        else:
            e.method = "Vay lãi cố định: không đổi theo lãi suất trong kỳ"
    else:  # cash, deposit, card, insurance, anything new
        e.method = {
            "cash": "Tiền VND: không chịu tác động giá",
            "deposit": "Tiền gửi VND lãi cố định: không chịu tác động giá",
            "card": "Dư nợ thẻ: không chịu tác động giá",
            "insurance": "Bảo hiểm: không mô hình hóa",
        }.get(cls, "Chưa có độ nhạy cho loại tài sản này")
    return e


def _months_label(months: float) -> str:
    if months < 1:
        return "1 tuần"
    return f"{months:g} tháng"

"""Write data/market_sources.json: every market series the app keeps, where it comes from (in order: the first that
answers is used) and which job fetches it (BRD_COMPLETION_PLAN F1, F-D2). Version 1 of the ``price_sources``
configuration (owner Admin); ``ticker_map`` is version 1 of the demo tickers → exchange symbols.

    uv run python scripts/make_market_sources.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "market_sources.json"

STOCKS = ["FPT", "TCB", "VCB", "MBB", "VNM", "HPG", "VHM", "MWG", "DGC", "SSI"]  # the demo's holdings (market.json)

JOBS = {
    "market_equity": {"label": "Cổ phiếu và VN-Index", "at": "15:45", "why": "HOSE đóng cửa 15:00; nến ngày"},
    "market_flows": {"label": "Giao dịch khối ngoại", "at": "16:00", "why": "số liệu cuối ngày"},
    "market_yields": {"label": "Lợi suất TPCP", "at": "17:30", "why": "HNX công bố đường cong cuối ngày"},
    "market_fx": {"label": "Tỷ giá USD/VND", "every": "1h", "why": "Vietcombank: tối đa 1 lần / 5 phút"},
    "market_world": {"label": "Thị trường thế giới", "every": "1h", "why": "giao dịch gần như suốt ngày; ~1 yêu cầu"},
    "market_crypto": {"label": "Tiền mã hóa", "every": "1h", "why": "xa dưới giới hạn công khai của Binance"},
    "market_gold": {"label": "Vàng SJC", "every": "1h", "why": "giá SJC đổi trong ngày"},
}


def s(sid, name, unit, job, sources, factor=None, note=None):
    out = {"id": sid, "name": name, "unit": unit, "job": job, "sources": sources}
    if factor:
        out["factor"] = factor
    if note:
        out["note"] = note
    return out


def src(source, symbol, scale=None):
    out = {"source": source, "symbol": symbol}
    if scale is not None:
        out["scale"] = scale
    return out


def series() -> list:
    out = [
        s("VNINDEX", "VN-Index", "điểm", "market_equity", [src("vndirect", "VNINDEX"), src("vietcap", "VNINDEX")],
          factor="VNINDEX"),
    ]  # fmt: skip
    for t in STOCKS:
        out.append(
            {
                **s(t, f"Cổ phiếu {t}", "VND", "market_equity", [src("vndirect", t, 1000), src("vietcap", t)]),
                "ticker": True,
            }
        )
    out += [
        s("FOREIGN_NET_HOSE", "Khối ngoại mua ròng trên HOSE", "VND", "market_flows", [src("cafef", "VNINDEX")],
          factor="FOREIGN_FLOW"),
        s("VN_GOV_3M", "Lợi suất TPCP 3 tháng (HNX)", "%", "market_yields", [src("hnx", "3M")], factor="VN_RATE",
          note="Thay thế cho lãi suất liên ngân hàng: cổng SBV không mở cho máy chủ này"),
        s("VN_GOV_1Y", "Lợi suất TPCP 1 năm (HNX)", "%", "market_yields", [src("hnx", "1Y")]),
        s("VN_GOV_5Y", "Lợi suất TPCP 5 năm (HNX)", "%", "market_yields", [src("hnx", "5Y")]),
        s("VN_GOV_10Y", "Lợi suất TPCP 10 năm", "%", "market_yields", [src("hnx", "10Y"), src("wgb", "58")],
          factor="VN_GOV"),
        s("USDVND", "Tỷ giá USD/VND (chuyển khoản)", "VND", "market_fx", [src("vcb", "USD"), src("msn", "avyufr")],
          factor="USDVND"),
        s("XAUUSD", "Vàng thế giới", "USD/oz", "market_world", [src("msn", "ck48ur")], factor="GOLD"),
        s("BRENT", "Dầu Brent", "USD/thùng", "market_world", [src("msn", "auvx3m")], factor="BRENT"),
        s("ACWI", "Cổ phiếu toàn cầu (ACWI)", "USD", "market_world", [src("msn", "a1mupr")], factor="GLOBAL_EQ"),
        s("SPX", "S&P 500", "điểm", "market_world", [src("msn", "a33k6h")]),
        s("US10Y", "Lợi suất TP Mỹ 10 năm", "%", "market_world", [src("msn", "a33knm", 0.1)], factor="US10Y"),
        s("EURUSD", "EUR/USD", "USD", "market_world", [src("msn", "av932w")]),
        s("USDJPY", "USD/JPY", "JPY", "market_world", [src("msn", "avyomw")]),
        s("GBPUSD", "GBP/USD", "USD", "market_world", [src("msn", "avyjhw")]),
        s("USDCAD", "USD/CAD", "CAD", "market_world", [src("msn", "avylur")]),
        s("USDSEK", "USD/SEK", "SEK", "market_world", [src("msn", "avyt52")]),
        s("USDCHF", "USD/CHF", "CHF", "market_world", [src("msn", "avyt7w")]),
        s("BTCUSD", "Bitcoin", "USD", "market_crypto", [src("binance", "BTCUSDT")], factor="BTC"),
        s("ETHUSD", "Ethereum", "USD", "market_crypto", [src("binance", "ETHUSDT")]),
        s("SJC", "Vàng miếng SJC (bán, TP.HCM)", "VND/lượng", "market_gold", [src("pnj", "SJC")]),
    ]  # fmt: skip
    return out


def main() -> None:
    out = {
        "note": "Public market sources, no account needed (probed 2026-10-16); unofficial, so each series names a "
        "fallback. Version 1 of the price_sources configuration. Written by scripts/make_market_sources.py.",
        "jobs": JOBS,
        "series": series(),
        "computed": {
            "DXY": {
                "name": "Chỉ số USD (DXY, tính theo công thức ICE)",
                "unit": "điểm",
                "factor": "DXY",
                "from": ["EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDSEK", "USDCHF"],
            },
            "SJC_GAP": {
                "name": "Chênh lệch vàng SJC so với thế giới",
                "unit": "%",
                "factor": "SJC_GAP",
                "from": ["SJC", "XAUUSD", "USDVND"],
            },
        },
        "assumed": ["RE_SPREAD", "FIN_SPREAD", "VN_HOUSE"],
        "ticker_map": {t: t for t in STOCKS},
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

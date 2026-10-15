"""Write data/factor_model.json: the 15-factor model the scenario engine (src/engine) runs on.

What comes from the BRD (§9.1–9.3) and is copied as written: the 15 factors, their shock sizes
S / M / L, how much of a move shows after 1 week / 3 months / 12 months, the priced-in multipliers,
the 40 % core-shock uncertainty, how the stressed regime is built, and the loadings by asset class.

What is ours and ASSUMED (giả định): every monthly volatility, every correlation, the stressed
volatility multipliers and the four stressed overrides, each stock's R² and FPT's USD revenue share.
The BRD estimates them from 55 months of Vietnamese data we do not have (docs/NEWS_IMPACT_PLAN.md,
blocker B1). They are plausible orders of magnitude, not estimates, and every screen that shows a
number from them says so. The engine refuses a model that is not symmetric, has a correlation
outside [−1, 1] or is not positive definite.

    uv run python scripts/make_factor_model.py
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "factor_model.json"

# id, name, group, unit, sizes S/M/L, realisation 1w/3m/12m, the BRD's parameter label,
# our monthly volatility (giả định), our stressed volatility multiplier (giả định, ≥ 1.2)
FACTORS = [
    ("US10Y", "Lợi suất trái phiếu Mỹ 10 năm", "intl", "bp", (15, 30, 60), (0.8, 1.0, 1.0), "Ước lượng", 25, 1.3),
    ("DXY", "Chỉ số USD (DXY)", "intl", "pct", (1, 2, 4), (0.8, 1.0, 1.0), "Ước lượng", 2.0, 1.3),
    ("GLOBAL_EQ", "Cổ phiếu toàn cầu", "intl", "pct", (3, 7, 15), (0.8, 1.0, 1.0), "Ước lượng", 4.5, 1.5),
    ("BRENT", "Giá dầu Brent", "intl", "pct", (5, 12, 25), (0.8, 1.0, 1.0), "Ước lượng", 9.0, 1.4),
    ("GOLD", "Giá vàng thế giới", "intl", "pct", (2, 5, 10), (0.8, 1.0, 1.0), "Ước lượng", 4.0, 1.3),
    ("BTC", "Bitcoin", "intl", "pct", (8, 20, 40), (0.9, 1.0, 1.0), "Giả định", 18.0, 1.3),
    ("USDVND", "Tỷ giá USD/VND", "domestic", "pct", (0.5, 1.5, 3), (0.4, 0.9, 1.0), "Ước lượng", 0.8, 1.5),
    (
        "VN_RATE",
        "Lãi suất VND điều hành, liên ngân hàng",
        "domestic",
        "bp",
        (25, 50, 100),
        (0.3, 0.8, 1.0),
        "Ước lượng",
        15,
        1.6,
    ),
    ("VN_GOV", "Lợi suất TPCP Việt Nam", "domestic", "bp", (15, 30, 60), (0.3, 0.8, 1.0), "Giả định", 15, 1.5),
    (
        "RE_SPREAD",
        "Chênh lệch tín dụng DN bất động sản",
        "domestic",
        "bp",
        (50, 150, 300),
        (0.2, 0.7, 1.0),
        "Giả định",
        40,
        2.0,
    ),
    (
        "FIN_SPREAD",
        "Chênh lệch tín dụng DN tài chính",
        "domestic",
        "bp",
        (20, 50, 100),
        (0.2, 0.7, 1.0),
        "Giả định",
        15,
        1.6,
    ),
    ("VNINDEX", "VN-Index", "domestic", "pct", (3, 7, 15), (0.7, 1.0, 1.0), "Ước lượng", 6.0, 1.6),
    (
        "FOREIGN_FLOW",
        "Dòng vốn ngoại trên HOSE",
        "domestic",
        "sd",
        (1, 2, 3),
        (0.7, 1.0, 1.0),
        "Ước lượng một phần",
        1.0,
        1.2,
    ),
    (
        "SJC_GAP",
        "Chênh lệch vàng SJC so với thế giới",
        "domestic",
        "pp",
        (2, 4, 8),
        (0.6, 1.0, 1.0),
        "Ước lượng",
        2.5,
        1.4,
    ),
    ("VN_HOUSE", "Giá nhà ở Việt Nam", "domestic", "pct", (1, 3, 6), (0.0, 0.3, 1.0), "Giả định", 1.5, 1.3),
]

# Normal-regime monthly correlations (giả định); pairs not listed are 0.
CORRELATIONS = [
    ("US10Y", "DXY", 0.40),
    ("US10Y", "GLOBAL_EQ", -0.20),
    ("US10Y", "GOLD", -0.30),
    ("US10Y", "BTC", -0.20),
    ("US10Y", "USDVND", 0.30),
    ("US10Y", "VN_GOV", 0.30),
    ("US10Y", "VNINDEX", -0.20),
    ("DXY", "GLOBAL_EQ", -0.30),
    ("DXY", "BRENT", -0.20),
    ("DXY", "GOLD", -0.40),
    ("DXY", "BTC", -0.30),
    ("DXY", "USDVND", 0.50),
    ("DXY", "VNINDEX", -0.25),
    ("DXY", "FOREIGN_FLOW", -0.30),
    ("GLOBAL_EQ", "BRENT", 0.30),
    ("GLOBAL_EQ", "BTC", 0.40),
    ("GLOBAL_EQ", "USDVND", -0.20),
    ("GLOBAL_EQ", "VNINDEX", 0.45),
    ("GLOBAL_EQ", "FOREIGN_FLOW", 0.35),
    ("BRENT", "GOLD", 0.15),
    ("GOLD", "BTC", 0.15),
    ("GOLD", "USDVND", -0.15),
    ("GOLD", "SJC_GAP", -0.30),
    ("USDVND", "VN_RATE", 0.30),
    ("USDVND", "VNINDEX", -0.35),
    ("USDVND", "FOREIGN_FLOW", -0.40),
    ("USDVND", "SJC_GAP", 0.20),
    ("USDVND", "VN_GOV", 0.25),
    ("VN_RATE", "VN_GOV", 0.60),
    ("VN_RATE", "RE_SPREAD", 0.30),
    ("VN_RATE", "FIN_SPREAD", 0.30),
    ("VN_RATE", "VNINDEX", -0.30),
    ("VN_RATE", "VN_HOUSE", -0.20),
    ("VN_GOV", "RE_SPREAD", 0.20),
    ("VN_GOV", "FIN_SPREAD", 0.30),
    ("VN_GOV", "VNINDEX", -0.25),
    ("RE_SPREAD", "FIN_SPREAD", 0.50),
    ("RE_SPREAD", "VNINDEX", -0.40),
    ("RE_SPREAD", "VN_HOUSE", -0.35),
    ("FIN_SPREAD", "VNINDEX", -0.30),
    ("VNINDEX", "FOREIGN_FLOW", 0.50),
    ("VNINDEX", "VN_HOUSE", 0.20),
]

# BRD 9.1: the stressed regime overrides four pairs after scaling (values giả định).
STRESSED_OVERRIDES = [
    ("VNINDEX", "FOREIGN_FLOW", 0.70),
    ("VNINDEX", "USDVND", -0.60),
    ("VNINDEX", "GLOBAL_EQ", 0.70),
    ("VNINDEX", "RE_SPREAD", -0.65),
]

MODEL = {
    "version": "FM-DEMO-2026-10",
    "status": "assumed",
    "note": (
        "Cỡ cú sốc, tỷ lệ thể hiện và cách tính theo BRD mục 9. Độ biến động, tương quan, R² và hệ số "
        "căng thẳng là giả định cho demo, chưa ước lượng từ dữ liệu."
    ),
    "horizons": {"1w": 0.25, "3m": 3, "12m": 12},  # months
    "priced_in": {"none": 1.0, "partial": 0.5, "full": 0.0},
    "core_uncertainty": 0.4,  # sd of a core shock, as a share of its size
    "stressed": {
        "scale": 1.4,
        "clip": 0.85,
        "min_vol_multiplier": 1.2,
        "overrides": [list(p) for p in STRESSED_OVERRIDES],
    },
    "factors": [
        {
            "id": f,
            "name": name,
            "group": group,
            "unit": unit,
            "sizes": dict(zip("SML", sizes)),
            "realisation": dict(zip(("1w", "3m", "12m"), real)),
            "brd_parameter": brd,
            "vol_month": vol,
            "stress_vol_multiplier": stress,
            "assumed": True,
        }
        for f, name, group, unit, sizes, real, brd, vol, stress in FACTORS
    ],
    "correlations": [list(p) for p in CORRELATIONS],
    "loadings": {
        "stock_r2": 0.35,  # share of a VN stock's variance VN-Index explains (giả định)
        "usd_revenue": {"FPT": 0.5},  # BRD 9.3 names FPT 50 %
        "fund_beta": {"equity": 1.0},  # sector beta of an equity fund (giả định)
        "fund_duration": {"bond": 2.0, "bond_long": 7.0, "bond_corporate": 2.5, "money": 0.0},  # BRD 9.3
        "gold_sjc_gap": 0.9,  # BRD 9.3
        "private_equity_vnindex": 0.5,  # BRD 9.3
    },
}


def main() -> None:
    OUT.write_text(json.dumps(MODEL, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

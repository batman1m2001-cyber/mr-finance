# Model validation, out of sample (BRD-RULE-MEAS-08)

Written by `scripts/validate_model.py` on 2026-10-16 from the market history stored by the
market jobs (FEAT-35). Method: [src/market/estimate.py](../../../src/market/estimate.py).

## Method

- Estimated with the months up to **2024-01** only (window from 2019-07, at most 55 months, at least 24; correlations shrunk 20 % toward zero, BRD §9.2).
- Scored on every month **after 2024-01 up to 2026-08**: is the factor's monthly move inside its P10–P90 band (±1.2816 σ)? 80 % is expected; BRD-RULE-MEAS-01 accepts 70–90 % (below: too narrow, above: too wide). The same over non-overlapping quarters (±1.2816 σ √3).
- Correlation drift: the mean absolute difference between each pair's correlation in and out of sample.
- The bands here are the model's unconditional ones (no scenario). Scoring each approved view's own bands as their horizons pass is FEAT-18 (BRD_COMPLETION_PLAN F3).

## Result

- Pooled monthly coverage: **85 %** over 372 factor-months — inside the 70–90 % band.
- Correlation drift: 0.226 on average over 66 pairs.

| Factor | Months | σ in sample | σ out of sample | Inside 1 month | Inside 3 months | Verdict |
|---|---|---|---|---|---|---|
| US10Y | 31 | 28.4 | 22.1 | 90 % | 90 % | dải rộng |
| DXY | 31 | 2.07 | 1.93 | 84 % | 90 % | đạt |
| GLOBAL_EQ | 31 | 5.44 | 3.2 | 97 % | 100 % | dải rộng |
| BRENT | 31 | 13.6 | 14.5 | 87 % | 90 % | đạt |
| GOLD | 31 | 4.24 | 5.62 | 68 % | 40 % | dải hẹp |
| BTC | 31 | 20.2 | 15 | 94 % | 90 % | dải rộng |
| USDVND | 31 | 1.15 | 1.07 | 81 % | 80 % | đạt |
| VN_RATE | 31 | 40.5 | 15.6 | 97 % | 90 % | dải rộng |
| VN_GOV | 31 | 29.9 | 12 | 100 % | 100 % | dải rộng |
| VNINDEX | 31 | 7.52 | 5.11 | 90 % | 90 % | dải rộng |
| FOREIGN_FLOW | 31 | 0.6 | 1.09 | 61 % | 40 % | dải hẹp |
| SJC_GAP | 31 | 3.83 | 5.07 | 74 % | 70 % | đạt |

Not validated (no free series; parameters stay assumed): RE_SPREAD, FIN_SPREAD, VN_HOUSE.

## Reading it

- **US10Y**: the band was too wide out of sample (σ 28.4 in sample, 22.1 after); the volatility differed between the two windows.
- **GLOBAL_EQ**: the band was too wide out of sample (σ 5.44 in sample, 3.2 after); the volatility differed between the two windows.
- **GOLD**: the band was too narrow out of sample (σ 4.24 in sample, 5.62 after); the volatility differed between the two windows.
- **BTC**: the band was too wide out of sample (σ 20.2 in sample, 15 after); the volatility differed between the two windows.
- **VN_RATE**: the band was too wide out of sample (σ 40.5 in sample, 15.6 after); the volatility differed between the two windows.
- **VN_GOV**: the band was too wide out of sample (σ 29.9 in sample, 12 after); the volatility differed between the two windows.
- **VNINDEX**: the band was too wide out of sample (σ 7.52 in sample, 5.11 after); the volatility differed between the two windows.
- **FOREIGN_FLOW**: the band was too narrow out of sample (σ 0.6 in sample, 1.09 after); the volatility differed between the two windows.

BRD-RULE-MEAS-08's own conclusion — use the model for VN-Index, and make FX and the SJC spread core shocks rather than inferring them — is a Model Risk decision; the table above is its evidence on this history.

## Data

| Series | First | Last | Points | Source |
|---|---|---|---|---|
| ACWI | 2020-01-02 | 2026-10-14 | 1704 | msn |
| BRENT | 2020-01-02 | 2026-10-14 | 1704 | msn |
| BTCUSD | 2020-01-01 | 2026-10-15 | 2480 | binance |
| DGC | 2020-01-02 | 2026-10-15 | 1686 | vndirect |
| ETHUSD | 2020-01-01 | 2026-10-15 | 2480 | binance |
| EURUSD | 2020-01-01 | 2026-10-14 | 1771 | msn |
| FOREIGN_NET_HOSE | 2020-04-21 | 2026-10-15 | 1306 | cafef |
| FPT | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| GBPUSD | 2020-01-01 | 2026-10-14 | 1771 | msn |
| HPG | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| MBB | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| MWG | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| SJC | 2020-01-03 | 2026-10-15 | 349 | pnj |
| SPX | 2020-01-02 | 2026-10-14 | 1702 | msn |
| SSI | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| TCB | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| US10Y | 2020-01-02 | 2026-10-14 | 1714 | msn |
| USDCAD | 2020-01-01 | 2026-10-14 | 1771 | msn |
| USDCHF | 2020-01-01 | 2026-10-14 | 1771 | msn |
| USDJPY | 2020-01-01 | 2026-10-14 | 1771 | msn |
| USDSEK | 2020-01-01 | 2026-10-14 | 1772 | msn |
| USDVND | 2020-02-07 | 2026-10-16 | 359 | vcb |
| VCB | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| VHM | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| VNINDEX | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| VNM | 2020-01-02 | 2026-10-15 | 1692 | vndirect |
| VN_GOV_10Y | 2020-01-03 | 2026-10-16 | 346 | hnx |
| VN_GOV_1Y | 2020-01-03 | 2026-10-16 | 346 | hnx |
| VN_GOV_3M | 2020-01-03 | 2026-10-16 | 346 | hnx |
| VN_GOV_5Y | 2020-01-03 | 2026-10-16 | 346 | hnx |
| XAUUSD | 2020-01-01 | 2026-10-14 | 1761 | msn |

Limitations: Vietcombank, PNJ and HNX are sampled weekly by the backfill (month-ends are the last sampled day); FOREIGN_FLOW is standardised over all stored months; cafef's foreign-flow history has gaps before 2022.

Estimate on all data to 2026-09: US10Y σ 25 → 29.09, DXY σ 2.0 → 2.17, GLOBAL_EQ σ 4.5 → 4.338, BRENT σ 9.0 → 11.99, GOLD σ 4.0 → 5.141, BTC σ 18.0 → 15.51, USDVND σ 0.8 → 1.272, VN_RATE σ 15 → 33.44, VN_GOV σ 15 → 27.73, VNINDEX σ 6.0 → 5.768, FOREIGN_FLOW σ 1.0 → 1.065, SJC_GAP σ 2.5 → 4.543.

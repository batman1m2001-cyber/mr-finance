# Forecast desk research scripts

The experiments behind [docs/FORECAST_DESK_PLAN.md](../../docs/FORECAST_DESK_PLAN.md) (closed 2026-10-26: the test on
the 2026-09 replay failed the gate). Kept as the record of what was tried; none of it runs in the app.

Run each from the repository root with the app venv. They read `out/lab/market.db` and `out/replay/<month>/`.
The pickles some scripts load (`cal_rows.pkl`, `odds_cal.pkl`, `odds_w.pkl`, `analog_rows_*.pkl`, `gbm_data.npz`)
are not committed; `calendar_eval.py`, `coef.py`, `analog_eval*.py` and `gbm_export.py` write them next to the scripts.

| Script | What it tested | Outcome |
|---|---|---|
| `baseline.py` | simple market statistics on the replays' moves | the fair baselines |
| `odds_eval.py`, `calendar_eval.py`, `train_ic.py`, `coef.py` | the statistical odds: IC of P(up), AUC of P(big) | P(big) AUC 0.73, P(up) near chance |
| `kb_fetch.py`, `analog_eval*.py` | headline analogs from 41,963 headlines | IC −0.1, dropped |
| `gbm_export.py`, `gbm_eval.py` | LightGBM against the logistic odds | no gain, dropped |
| `make_tracks.py`, `score_month.py` | odds / fused tracks for the lab | odds_all frozen for the test |
| `fuse_fit.py` | ridge-logistic learned fusion, fit July, test August | 43–54%, dropped |
| `pnl_walk.py` | walk-forward weekly long/short P&L 2023 → 2026-09 | written, not run |

`results/` holds the lab outputs (`lab_dev_*.json`, `lab_test.json`) and the desk iterations' logs.

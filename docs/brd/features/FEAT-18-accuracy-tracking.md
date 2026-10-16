# FEAT-18 — Accuracy over time and the measurement reports

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-15, BRD-KPI-01, BRD-KPI-03, BRD-KPI-04, BRD-RULE-MEAS-01, BRD-RULE-MEAS-02, BRD-RULE-MEAS-03, BRD-RULE-MEAS-05, BRD-RULE-WF-09, BRD-NFR-02 |
| Users | CIO; Compliance reads the reports |
| Screens | [SCR-CIO-12](../ux/screens/cio.md#scr-cio-12--độ-chính-xác-accuracy-over-time) Độ chính xác, [SCR-CIO-13](../ux/screens/cio.md#scr-cio-13--đo-lường-measurement-reports) Đo lường |
| Code | `src/measure/` (`realised`, `backtest`, `forecasts`, `reports`, the `accuracy_score` job); `GET /api/accuracy`, `GET /api/measure` |
| Tests | `tests/test_accuracy.py` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## What the BRD asks
For each factor and horizon, the share of realised moves inside the forecast P10–P90 band (accept 70–90 %, at
least 24 observations before concluding), and the direction hit rate — after 1 week, 3 months and 12 months
(MEAS-01/02, KPI-03/04). Monthly: misses with causes (MEAS-03), rubber-stamping (MEAS-05), news to RM ≤ 2 h
(KPI-01, WF-09), news to inbox ≤ 10 min and the CIO agent ≤ 15 min (NFR-02).

## What is built

**The realised move** (`measure/realised.py`): a factor's move between two days from its stored series
([FEAT-35](FEAT-35-market-data-layer.md)), in its unit — % for levels, ×100 for yields (basis points), points for
the SJC gap, and for foreign flows the period's net buying less the average month's, over the monthly sd. A day
without a point takes the latest before it, up to 7 days; beyond that there is no data.

**The model on history, walking forward** (`measure/backtest.py`). At every origin the model is estimated from the
months already ended (the same estimation as [FEAT-07](FEAT-07-scenario-engine.md) F2: 55 months, at least 24) and
only that is used:

- *Band*: with no scenario the engine's band for a factor is centred on 0 with sd = monthly volatility ×
  √months × the BRD's realisation share at the horizon. Inside P10–P90 or not.
- *Direction*: the engine's step 2 — the factor inferred from what the other factors actually did over the
  period (Σfc Σcc⁻¹ Δc). Right sign or not. This is the engine's direction when the CIO calls the core shocks
  right; the views' own calls are below.
- Origins every 7 days (1 week) and every month end (3, 12 months: these periods overlap, so the observations are
  not independent — said on the page). On 2022-01 → 2026-10 data (the live history): pooled coverage 72 % (1 week), 77 % (3 months),
  75 % (12 months); VN-Index direction 57 %, 72 %, 96 %. Gold and the VN yields are too narrow at most horizons.

**The views' own forecasts** (`measure/forecasts.py`). On approval each view's branches go through
`engine.factor_bands` with the model in force: for all 15 factors and the 3 horizons, the expected move and
P10/P50/P90 from the approval day to its due day (+7, +91, +365 days). The `accuracy_score` job (18:30 daily,
after the market jobs) records any approved view not yet recorded (marked “ghi lại sau khi duyệt”) and scores every
forecast whose due day the factor's data has reached: realised move, inside the band, direction right (when the
forecast had one). Factors without a series are closed as “không có dữ liệu”; so is data still missing 30 days
after the due day. A view withdrawn or superseded later stays scored: the record is of what was approved.

**The measurement reports** (`measure/reports.py`), monthly:

- MEAS-03: high-relevance news never grouped into an event — dismissed by the CIO, held for Compliance, or more
  than a day in the inbox — and events that never reached families: no view, view not approved, approved without
  an effective run. “Important” is read as relevance “high” here; KPI-02 uses the reference reading of Q-07 below.
- MEAS-05: per approval, the CIO's minutes from ready-for-approval to approved; the share approved without an
  edit; approvals under 2 minutes (our signal, labelled as such — the BRD gives no threshold).
- KPI-01 / WF-09: per effective run, hours from the event's first news being published to the run being
  effective, against 2 h; events the CIO flagged urgent against 30 min (`news/urgent.py` proposes; the CIO decides).
- KPI-02: important stories in an independent reference (`news/reference.py`) collected by our feeds, by day and
  month, against 95 %.
- NFR-02: minutes from publication to the inbox (news published after the ingest job started), and each CIO agent
  run's duration, with the share meeting 10 and 15 minutes.

## Limits
- The views' record is short: the demo's first approvals were on 2026-10-15, so the first 1-week scores land on
  2026-10-22 and nothing reaches 24 observations for a long time. The page says “chưa đủ 24 quan sát”.
- The three assumed factors (RE_SPREAD, FIN_SPREAD, VN_HOUSE) have no free series and are never scored.

## Do not confuse with
The “Hiệu quả tư vấn” pages (FEAT-28) show a **mock** advisory track record from `data/advisory.json`. They are
not BR-15 and are not evidence of accuracy (Q-19).

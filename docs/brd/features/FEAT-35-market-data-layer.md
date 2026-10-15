# FEAT-35 — Market data layer

| | |
|---|---|
| Type | BRD capability (enabler for BR-15, ENG-11, MEAS-01/02/08, KPI-03/04) |
| Requirements | BRD-RULE-ENG-11 (provenance), BRD-BR-15, BRD-KPI-03, BRD-KPI-04, BRD-RULE-MEAS-01, BRD-RULE-MEAS-02 (history they need) |
| Users | CIO, Admin |
| Entry points | [SCR-CIO-11](../ux/screens/cio.md#scr-cio-11--dữ-liệu-thị-trường-market-data) `#/cio/mo-hinh/du-lieu`, Admin `#/admin/du-lieu`; `GET /api/market`, `GET /api/market/series`; jobs `market_equity`, `market_flows`, `market_yields`, `market_fx`, `market_world`, `market_crypto`, `market_gold`, `market_backfill` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Real market history for the model's factors, fetched from public sources on a schedule and kept in the app's
database, so the model can be estimated (F2) and forecasts scored (F3). Owner's re-architecture, 2026-10-16: every
outside source has its own job; the app reads SQLite only ([ADR-0021](../decisions/ADR-0021-market-data-through-scheduled-jobs.md)).

## Behaviour
1. Each job runs its op on its clock (local time, Asia/Ho_Chi_Minh): `market_equity` 15:45, `market_flows` 16:00,
   `market_yields` 17:30, `market_fx`, `market_world`, `market_crypto`, `market_gold` hourly. The cadence follows
   each source's rate limit and when its data changes (data/market_sources.json `jobs`).
2. For each series of the job, the sources are tried in order; the first that answers with points is used. A tick
   asks from the last stored day (at most 10 days back). The MSN series of a run go in one request; the HNX
   curve is asked once a day for all tenors.
3. Points go to `market_series` (one per series and day; a later fetch replaces the day's point) with the
   source, URL and fetch time. Every fetch is a `source_runs` row: the source used, the sources tried with their
   errors, points kept, error. A day a per-day source has not published yet (PNJ answers 422 for today) is
   skipped; nothing new within three days is not an error (weekends).
4. `market_backfill` (on demand: `operonx run market_backfill [--set since=…]`) fetches every series from 2020-01;
   the per-day sources (Vietcombank, PNJ, HNX) are sampled weekly, with a pause between requests.
5. `factor_series` turns the series into the 15 factors' month-end moves in their units (pct, bp, pp, sd), with a
   provenance label each: market data and its source, computed (DXY by ICE's formula, SJC gap), a labelled proxy
   (VN_RATE ← HNX 3-month), or “Giả định” (RE_SPREAD, FIN_SPREAD, VN_HOUSE: no free source).

## Sources (probed 2026-10-16, no account)
VNDirect → Vietcap (VN-Index, 10 stocks), cafef (foreign net buying on HOSE), HNX → worldgovernmentbonds (yields),
Vietcombank → MSN (USD/VND), MSN (gold, Brent, ACWI, S&P 500, US 10-year, six currencies), Binance (BTC, ETH),
PNJ (SJC bars). giavang.org, the planned SJC fallback, no longer serves data to this server, so SJC has one source.
Details and blocked sources: [integrations](../architecture/integrations.md).

## Rules and validation
- The sources and their order are the `price_sources` configuration (owner Admin, FEAT-14); an unknown source is
  refused. `ticker_map` maps the demo's tickers to exchange symbols.
- The demo families keep the mock price snapshot (F-D1); this history feeds estimation and scoring only.

## API and data
`GET /api/market` (staff): jobs with cadence, last run, last success, last error; series with coverage, last value,
source and the last 120 days; factors with provenance. `GET /api/market/series?id=&from=`: one stored or computed
series. Tables `market_series`, `source_runs` (state file).

## Implementation
`src/market/sources.py` (adapters), `fetch.py` (fallback, memo, runs), `store.py`, `factors.py`, `ops.py`,
`graph.py`; jobs in `app/main.py`; `scripts/make_market_sources.py` → `data/market_sources.json`;
`scripts/market_smoke.py` (live check); UI `web/pages/market.js`.

## Acceptance and tests
`tests/test_market.py` (18 tests on responses recorded from every source): each adapter's format and units; a failed
day skipped; fallback recorded; every source failing recorded as the job's error; one MSN request for the world job;
one HNX request a day for all tenors; jobs scheduled; DXY and SJC gap formulas; moves per unit; provenance; the
configuration owned by Admin and applied; the API reads SQLite only. Live: `scripts/market_smoke.py` (all 44 source entries of the 31 series
answered on 2026-10-16).

## Limitations
- The sources are unofficial and may change format; the smoke script and the job errors on the page show it.
- SJC has no fallback; RE_SPREAD, FIN_SPREAD and VN_HOUSE have no free source (F-D3).
- No alert yet when a job keeps failing (F7).

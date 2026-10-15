# ADR-0021 — Market data comes from public sources through scheduled jobs into SQLite

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** owner, 2026-10-16 (“services that crawl/fetch data from public internet … with period … and save them
  to a sqlite”); docs/BRD_COMPLETION_PLAN.md F-D1, F-D2, F-D3, F-D11

## Context

The model's parameters were all assumed because the demo had no price history (Q-22); BR-15, MEAS-01/02 and
KPI-03/04 were blocked on it. Free public sources exist for 12 of the 15 factors, none of them official or
contractual.

## Decision

- Each kind of data is one operonx op in its own graph and scheduled `Job`, with a cadence from the source's rate
  limit and when its data changes. Each source sits behind an adapter; each series names its sources in order
  (`price_sources` configuration, owner Admin) and the first that answers is used.
- Every point keeps its source, URL and fetch time; every fetch is recorded with what was tried.
- The app reads the stored data only (F-D11); no request reaches an outside source.
- The suite never touches the network: adapters are tested on recorded responses; `scripts/market_smoke.py` checks
  the live sources.
- The demo families keep their mock prices (F-D1); the history feeds estimation (F2) and scoring (F3).

## Consequences

- A source that changes format or blocks the server shows as a job error and falls back; the page shows which.
- Three factors stay assumed (F-D3); VN_RATE uses a labelled proxy.
- A bank deployment replaces the adapters with licensed feeds behind the same tables.

# FEAT-18 — Accuracy over time

| | |
|---|---|
| Type | BRD capability — **not built** |
| Requirements | BRD-BR-15, BRD-KPI-03, BRD-KPI-04, BRD-RULE-MEAS-01, BRD-RULE-MEAS-02 |
| Users | CIO, Model Risk |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## What the BRD asks
For each factor and horizon, the share of realised moves inside the forecast P10–P90 band (accept 70–90 %, at
least 24 observations), and the direction hit rate — after 1 week, 3 months and 12 months.

## Why it is not built
It needs time to pass and realised market data: the demo's market is a mock snapshot (2026-10-09). It is
**blocked** on a price history feed, then planned (news plan N5).

## Do not confuse with
The “Hiệu quả tư vấn” pages (FEAT-28) show a **mock** advisory track record from `data/advisory.json`. They are
not BR-15 and are not evidence of accuracy (Q-19).

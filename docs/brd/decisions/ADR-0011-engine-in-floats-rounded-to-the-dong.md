# ADR-0011 — The engine computes in floats and rounds to the dong once

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** docs/NEWS_IMPACT_PLAN.md A10; Q-13

## Context

NFR-05 forbids floats for balances; the BRD's own scenario layer uses floats (F22).

## Decision

- Balances and holdings are integers. The engine (`src/engine`) computes in floats and rounds every VND result in one place; contributions use largest-remainder rounding so they add up to the total exactly.
- `GET /api/runs/{id}/verify` recomputes from the frozen snapshot and must match to the dong (NFR-04).

## Consequences

- Determinism is tested (`test_the_same_inputs_give_the_same_numbers_to_the_dong`, `test_a_run_recomputes_to_the_dong_and_tampering_is_found`).

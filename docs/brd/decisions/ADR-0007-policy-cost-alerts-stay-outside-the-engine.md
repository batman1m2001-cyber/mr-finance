# ADR-0007 — Policy-cost alerts stay outside the scenario engine

- **Status:** accepted (partly implemented)
- **Date:** 2026-10-15
- **Sources:** docs/NEWS_IMPACT_PLAN.md A6; Q-03

## Context

BR-08 makes the engine the only machine for alerts. The pre-BRD alerts (`src/impact`) mix cash costs (property tax, transfer tax, PIT relief) with price moves (gold policy, market upgrade, rates, FX, infrastructure).

## Decision

- Cash-cost rules are not price moves: they stay as “Chi phí chính sách”, outside the impact ranking and the RM pre-review.
- Price-moving rules and the stress tests should become core-shock presets run by the engine (news plan N5, not started).

## Consequences

- Until N5, the client overview's “Headline News” card shows point-rule numbers next to the engine's results (Q-03).
- 2026-10-16 (BRD completion F10): that card is now “Chính sách và dự án”, labelled as the policies' own rules with a link to the engine's Tác động thị trường; goals take the engine's VND impact (BR-08), so ranking, the RM list, goals and explanation are all the engine's.

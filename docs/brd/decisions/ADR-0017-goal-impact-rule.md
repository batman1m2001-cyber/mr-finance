# ADR-0017 — Goal impact (FR-404): goals draw on financial assets in date order; levels as in goals planning

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** BRD §6.4 FR-404; Q-11; owner decision D-02 (“do what you think it's best”, 2026-10-16)

## Context

FR-404 asks, per run, each goal's funding ratio before and after with a level Đạt / Theo dõi / Thiếu, and gives
neither the thresholds nor what funds a goal. No asset is earmarked to a goal in the data. Goals planning
(FEAT-26) already rates a goal by the monthly saving it needs over the monthly surplus (≤ 0.6, ≤ 1, above), but
counts only cash, deposits and liquid funds above a 6-month reserve as available.

## Decision

- Keep the rule built on 2026-10-15 (`src/apply/goals.py`): a family's dated goals draw, in date order, on its
  financial assets (cash, deposits, funds, bonds, stocks, gold, crypto); after = the same plus the run's 3-month
  expected change on those holdings; the level is the goals-planning rule (≤ 0.6 Đạt, ≤ 1 Theo dõi, above Thiếu).
- Not the goals-planning pool: it leaves out stocks, bonds and gold, so news on those markets could never move a
  goal, which defeats FR-404's purpose.
- The page no longer says the rule waits for the CIO.

## Consequences

- The demo families' financial assets cover their goals several times over (C01: 14.7 tỷ against 1.885 tỷ), so
  every demo goal stays Đạt before and after. That is the correct answer for them, not a defect; the page shows
  the pool before → after so the margin is visible.
- A bank policy (earmarked assets, other thresholds) would replace this rule by a new ADR; `goal_impacts` is the
  one place to change.

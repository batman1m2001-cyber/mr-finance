# FEAT-29 — Financial Pulse, Wealth Map and Money Flow

| | |
|---|---|
| Type | Proposed extension (redesign kit), approved for planning 2026-10-15 — **not built** |
| Requirements | KIT-UX-01, KIT-UX-02, KIT-UX-03, KIT-UX-06, KIT-UX-07; must keep BRIEF-DASH-01…07 |
| Users | Client, RM |
| Plan | [docs/REDESIGN_KIT_PLAN.md](../../REDESIGN_KIT_PLAN.md) phase **K2**, decision D4 |
| Status | see [traceability](../requirements/requirements_traceability.md) §4 |

## Intended behaviour (from the plan, not yet built)
- `GET /api/flows?client&scope&month` aggregates **transaction rows only**: inflow categories (salary, rent,
  pension) → outflow categories (living, card, loan, school, health, rent_out) + “Còn lại” (or “Thiếu hụt”). No
  inferred flows and no investment band — the fixtures hold no investment purchases.
- Example from the data (C01, personal, September 2026): salary 120.4 tr in → living 17.6, card 34.8, home loan
  38.0 out → 30.0 tr left.
- A Sankey drawn in SVG by `web/charts/` (no new library), click a band to see its rows; a KPI strip (net worth
  and change, monthly in/out/left, liquidity months, risk signal); allocation with drill-down.
- Every block of today's overview (FEAT-21) stays reachable — moved, not removed — with a checklist.

## Acceptance (plan gate)
Bands add up to the transaction totals to the dong (test); the overview checklist ticked item by item;
reduced-motion shows a static chart; desktop and phone screenshots in light and dark.

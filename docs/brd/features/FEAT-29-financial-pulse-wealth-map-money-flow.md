# FEAT-29 — Financial Pulse, Wealth Map and Money Flow

| | |
|---|---|
| Type | Extension (redesign kit), built 2026-10-16 (plan phase K2) |
| Requirements | KIT-UX-01, KIT-UX-02, KIT-UX-03, KIT-UX-06, KIT-UX-07; keeps BRIEF-DASH-01…07 |
| Users | Client, RM |
| Entry points | [SCR-CL-08](../ux/screens/client.md#scr-cl-08--toàn-cảnh-pulse-wealth-map-money-flow) — client Tổng quan → Toàn cảnh, RM Khách hàng → Toàn cảnh; `POST /api/flows` |
| Plan | [docs/REDESIGN_KIT_PLAN.md](../../REDESIGN_KIT_PLAN.md) phase **K2**, decision D4 |
| Status | see [traceability](../requirements/requirements_traceability.md) §4 |

## Behaviour
- **Money Flow:** `flows_flow` (`POST /api/flows {client_id, scope, month?}`) sums one month's **transaction rows
  only**: inflow categories → the month → outflow categories + “Còn lại” (or a “Thiếu hụt” band in when out > in).
  No inferred flow, no investment band (the fixtures hold no purchases). Each band returns its rows. Default month:
  the latest with rows. Example (C01, personal, 09/2026): Lương 120 tr → Trả nợ vay 38, Thanh toán thẻ 34,8, Chi
  tiêu sinh hoạt 17,6 → Còn lại 30 tr.
- **Sankey** (`web/charts/charts.js::sankey`): SVG, no library, no motion; every band is focusable (Enter opens
  it), hover shows value and share; below it, a table of every band (the chart's table view); a band opens its
  transactions; a month picker.
- **Financial Pulse:** six tiles — net worth and month change, the month's money in, out, left, the liquidity
  reserve with its status, the stress-loss estimate against the accepted limit with its status. All from
  `POST /api/dashboard` and the flows answer; the page computes only sums of returned numbers.
- **Wealth Map:** a 100 % bar of assets by class (cash folded into deposits, as on the allocation table), values,
  shares, price date; a class opens its holdings (with owner in family scope). Debts are stated beside it.
- The former overview (FEAT-21) is unchanged under **Chi tiết** — nothing moved or removed; Toàn cảnh links to it.

## Implementation
`src/flows/{ops,graph}.py`, service `flows` in `app/main.py`; `web/pages/pulse.js`; styles `.kpis`, `.wmap`,
`.sankey` in `web/core/tokens.css`; nav in `web/shell.js`.

## Acceptance and tests
`tests/test_flows.py` (bands = rows to the dong, C01 09/2026 = 30.0 tr left, default month, family adds the
spouse, bad requests refused, endpoint). UI: desktop and phone, light and dark, family scope, band click, map
drill-down, month switch — no console error, no horizontal scroll (2026-10-16).

## Limitations
- Months are the fixtures' 12 (10/2025–09/2026); flows of statement uploads and declarations are not included
  (they carry no transactions).
- No automated UI test (KIT-UX-01, 03 stay `implemented_unverified`).

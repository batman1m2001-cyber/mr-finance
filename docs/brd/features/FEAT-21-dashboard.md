# FEAT-21 — The overall dashboard

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-DASH-01…07, BRIEF-DATA-04, BRIEF-DATA-05 |
| Users | Client; RM (Khách hàng → Tổng quan) |
| Entry points | [SCR-CL-01 Tổng quan](../ux/screens/client.md#scr-cl-01--tổng-quan-overview); `POST /api/dashboard {client_id, scope, months}` |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Purpose
The brief's selling point: net worth and what makes it up, how it performs, how much risk and liquidity there
is, and the money coming in and going out over the next 12–36 months.

## Behaviour (`dashboard_flow`, one op per section over the consolidated holdings)
- `net_worth` — assets − debt, the month change, the trust mix (share verified / statement / declared).
- `allocation` — by asset class, value, share, P&L against cost.
- `performance` — realised (year to date) and unrealised P&L, return against the client's benchmark (VN-Index).
- `drawdown` — the loss in a bad-market stress against the client's accepted drawdown (from the last risk test,
  else the profile); “An toàn / Gần ngưỡng / Vượt ngưỡng”.
- `concentration` — a sector, area or issuer above its share threshold (e.g. one property area > 35 %).
- `liquidity` — cash, deposits and liquid funds (not stocks) as months of spending; safe mark 6 months.
- `cashflow` — the past months as they happened and a 12/24/36-month forecast: recurring items found in the
  transactions (salary monthly, school fees by term; a card balance paid once), maturities, coupons,
  instalments, known dated events; large payments flagged.
- The page also shows the source groups (“Our Wealth at Techcombank”, “Custody around the world”,
  “Self-managed”: tiers mapped to titles in `web/pages/detail.js`; since 2026-10-20 the Vietnamese name leads — “Tại hệ sinh thái Techcombank”, “Lưu ký bên ngoài”, “Bạn tự quản lý” — and the English one is the small line) and a “Headline News” card from the policy alerts
  (FEAT-25).

## Implementation
`src/dashboard/{graph,ops,_calendar}.py`; UI `web/pages/detail.js` (Chi tiết; was tab `overview`).

## Acceptance and tests
`tests/test_dashboard.py` (12 tests, e.g. `::test_net_worth_is_assets_less_debt_with_its_month_change_and_confidence`,
`::test_liquidity_counts_cash_deposits_and_liquid_funds_not_stocks`, `::test_recurring_items_are_found_monthly_and_by_school_term`,
`::test_the_family_view_is_the_household_sum`); `tests/test_demo.py::test_the_five_minute_demo`.

## Limitations
The “Headline News” card shows point-rule impacts, not the engine's (Q-03). Since 2026-10-16 this page is
“Tổng quan → Chi tiết”; “Toàn cảnh” (FEAT-29) opens first and links here.

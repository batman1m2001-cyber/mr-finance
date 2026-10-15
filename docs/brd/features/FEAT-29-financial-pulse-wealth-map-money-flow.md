# FEAT-29 — Financial Pulse, Wealth Map and Money Flow

| | |
|---|---|
| Type | Extension (redesign kit), built 2026-10-16 (plan phase K2); board look 2026-10-16 (UI redesign R2) |
| Requirements | KIT-UX-01, KIT-UX-02, KIT-UX-03, KIT-UX-06, KIT-UX-07, OWN-UI-01; keeps BRIEF-DASH-01…07 |
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
- **Sankey** (`web/charts/charts.js::sankey`): SVG, no library; one fixed colour per category (salary blue,
  loans red, cards amber, living orange, “Còn lại” green, “Thiếu hụt” red), each band strongest at its own node,
  icon chips beside the labels on wide screens; every band is focusable (Enter opens it), hover shows value and
  share. Picking a band highlights it, dims the rest, opens its transactions and sends three dots along it three
  times (Web Animations on `transform`, tracked by `motion.js` so a hidden tab pauses them; none under reduced
  motion), then stops. Below: three ratios (share saved or overspent, out ÷ in, the largest spending group) and
  the table of every band (the chart's table view). A month picker.
- **Financial Pulse:** four cards with one small chart each — **Tài sản ròng** (value, month change, and the three
  asset classes that moved it most: Σ value − value last month per class, debts against it; the split adds up to
  the month change), **Dòng tiền** (left or short this month, in and out, the share saved, paired in/out bars for
  the last six months from the dashboard's 12-month history, the picked month in full colour), **Thanh khoản dự
  phòng** (value, months of spending, status, a ring of its share of assets), **Rủi ro khi thị trường xấu** (stress
  loss % against the accepted limit on a gauge, status, the loss in VND). All from `POST /api/dashboard` and the
  flows answer; the page computes only sums and shares of returned numbers.
- **Wealth Map:** a donut of assets by class (cash folded into deposits, as on the allocation table) with the total
  inside, a legend with icon, value and share, price date; a class (segment or legend row) opens its holdings (with
  owner in family scope). Debts are stated beside it.
- **Goals** (since R2): each followed goal from `POST /api/goals` — status, what it needs and by when, a progress
  bar, the gap and what is set aside for it; a link to Kế hoạch.
- The former overview (FEAT-21) is unchanged under **Chi tiết** — nothing moved or removed; Toàn cảnh links to it.

## Implementation
`src/flows/{ops,graph}.py`, service `flows` in `app/main.py`; `web/pages/pulse.js`; `web/charts/mini.js` (ring,
donut, gauge, progress); styles `.kpis`, `.pcard`, `.contrib`, `.ratios`, `.wmap2`, `.goals`, `.sankey` in
`web/core/tokens.css`; nav in `web/shell.js`.

## Acceptance and tests
`tests/test_flows.py` (bands = rows to the dong, C01 09/2026 = 30.0 tr left, default month, family adds the
spouse, bad requests refused, endpoint). `tests/ui/test_pulse.py` (3): the class split, donut parts, goals and
feed items equal the APIs' (and the split sums to the month change); a picked band flows three times, pauses
with a hidden tab and ends; reduced motion picks without dots. Plus the route sweep at 1440 and 390 px.

## Limitations
- Months are the fixtures' 12 (10/2025–09/2026); flows of statement uploads and declarations are not included
  (they carry no transactions).
- No net-worth trend line (the board shows one): prices carry only now, last month and the year start, so a
  series would be invented (UI redesign plan §1).

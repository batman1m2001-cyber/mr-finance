# FEAT-26 — Life scenarios, stress tests and goals planning

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-SCEN-01…03, BRIEF-FLOW-01 |
| Users | Client, RM |
| Entry points | [SCR-CL-03 Kế hoạch](../ux/screens/client.md#scr-cl-03--kế-hoạch-wealth-planning-advisor); `POST /api/scenario {client_id, scenario, params?, scope?}`, `POST /api/goals {client_id, scope?}`, `GET /api/scenarios` |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Behaviour
- **`scenario_flow`** — 9 life events (`tuition`, `retire_early`, `sell_home`, `leverage_buy`, `pass_on`,
  `business_cash`, `medical`, `emigrate`, `wedding`) and 5 stress tests (`bond_crisis`, `re_freeze`, `vni_30`,
  `rates_up`, `usd_up`) on the client's own holdings, with defaults from their data and editable parameters;
  each answers with numbers, before/after, and a **light** and a **heavy** option. Stress tests are measured
  against the drawdown limit.
- **`goals_flow`** (“Wealth Planning Advisor”, from PR #13) — every life goal: need, what the client has for it,
  the gap, a status (ON_TRACK / AT_RISK / OFF_TRACK by the ratio of the monthly saving needed to the monthly
  surplus: ≤ 0.6, ≤ 1, above), ranked actions, and month-by-month tracking (start of year, last month, now).
- An option can be sent to the RM queue (FEAT-27).

## Implementation
`src/scenarios/{graph,ops,_sim}.py` (`SCENARIOS`); UI `web/pages/plan.js` (Kế hoạch; was tab `scenarios`).

## Acceptance and tests
`tests/test_scenarios.py` (10 tests, e.g. `::test_every_scenario_runs_for_every_client_in_both_views`,
`::test_every_client_has_goals_with_a_gap_a_status_and_ranked_actions`, `::test_the_money_maths`).

## Limitations
- The stress tests do not use the BRD engine (N5, ADR-0007).
- Goals here and the goal branch's goals (FEAT-10) are separate lists; the regulation note is not on these cards
  (Q-20).

# FEAT-24 — The risk-appetite test

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-RISK-01…05 |
| Users | Client (Mục tiêu & kịch bản → Khẩu vị rủi ro) |
| Entry points | [SCR-CL-04](../ux/screens/client.md#scr-cl-04--khẩu-vị-rủi-ro-risk-test); `POST /api/risk {client_id, answers}` |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Behaviour (`risk_flow`)
Rules, not a model ([ADR-0015](../decisions/ADR-0015-decisions-of-the-first-build-plan.md) D3). 13 situational
questions; 8–12 asked on any path; the drop question uses the client's own portfolio; a fearful answer leads to a
smaller fall, a calm one to a crash; business and big-expense questions only for who has them. Tolerance from
the answers; capacity from the data (liquidity, debt service, leverage, dependents, age, horizon, income); the
profile is the lower of the two, one level lower again when what the client did in the April dip contradicts
what they say. Five personas: Bảo toàn, Thận trọng, Cân bằng, Tăng trưởng, Mạo hiểm. The result sets the
dashboard's drawdown limit.

## Implementation
`src/risk/{graph,ops,_bank}.py`.

## Acceptance and tests
`tests/test_risk.py` (8 tests, e.g. `::test_every_path_asks_8_to_12_questions`, `::test_wanting_more_than_one_can_bear_is_said_out_loud`,
`::test_who_says_bold_but_sold_in_the_dip_is_stepped_down`, `::test_the_result_sets_the_dashboard_s_drawdown_limit`).

## Limitations
No re-ask on life events, market moves or every 6 months (BRIEF-RISK-04, Q-16).

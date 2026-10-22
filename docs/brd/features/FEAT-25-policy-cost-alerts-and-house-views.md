# FEAT-25 — Policy-cost alerts and house views

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-IMPACT-01…05, BRIEF-ALERT-01, BRIEF-ALERT-02, BRIEF-DASH-07 |
| Users | Client (Headline News → Chi phí chính sách since 2026-10-22, [ADR-0037](../decisions/ADR-0037-the-clients-four-sections-carry-the-banks-names.md); its Wealth Check reads green ahead of VN-Index, red behind), RM |
| Entry points | [SCR-CL-06 Chi phí chính sách](../ux/screens/client.md#scr-cl-06--chi-phí-chính-sách-policy-costs), the overview's “Headline News”; `POST /api/alerts {client_id, scope?}`; job `policy_sweep` 07:00; `GET /api/views` (house views) |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Behaviour (`alerts_flow`)
19 dated factors in `data/factors.json` (the brief's 14 policies, two macro moves, three infrastructure
projects), each with a legal status (→ probability: draft low, consultation medium, passed high), a source line
and a rule (`src/impact/_rules.py`, 16 rule types: which holdings it touches, the sensitivity). Impact = exposure
× sensitivity × probability, in VND and as a share of net worth; severity high from 1 %, medium from 0.3 %, else
low; risks and opportunities. The latest result per client is kept; the `policy_sweep` job reruns every client
at 07:00. House views (8 mock research-house forecasts, `data/views.json`) are matched to the client's holdings
and shown beside the alerts.

## Relation to the BRD
These are not the BRD's engine (Q-03, [ADR-0007](../decisions/ADR-0007-policy-cost-alerts-stay-outside-the-engine.md)):
cash-cost rules stay here; price-moving ones should move to the engine (N5).

## Implementation
`src/impact/{graph,ops,_rules}.py`; `app/web.py::views`; UI `web/pages/policy.js` (was tab `alerts`).

## Acceptance and tests
`tests/test_impact.py` (10 tests, e.g. `::test_impact_is_exposure_times_sensitivity_times_probability`,
`::test_severity_follows_the_share_of_net_worth`, `::test_the_policy_sweep_runs_at_seven_every_morning`);
`tests/test_app.py::test_the_house_views`.

## Limitations
- Legal statuses are a snapshot to check before any real use (BRIEF-ALERT-02; every page says so).

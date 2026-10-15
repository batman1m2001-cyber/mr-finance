# FEAT-12 — Roles and separation of duties

| | |
|---|---|
| Type | BRD capability (demo form) |
| Requirements | BRD-RULE-ROLE-01…06, BRD-RULE-SEC-01, BRD-RULE-SEC-02, BRD-RULE-SEC-04, BRD-RULE-SEC-10 |
| Users | Everyone |
| Entry points | The role switcher in the shell ([information architecture](../ux/information_architecture.md)); `GET /api/agents` lists the demo users |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Make sure each action is done only by the role allowed to do it, and that the steps that need two people get
two people — in a demo with no sign-in.

## Behaviour
- Demo users (`src/control/roles.py`): `cio` (Trần Quang Huy), `cio2` (Lê Thu Hà), `rm01` (Phạm Gia Bảo),
  `compliance` (Đỗ Minh Châu), `compliance2` (Vũ Hải Nam), `admin`. The UI sends the active role's user id
  with each action.
- News-impact actions call `roles.require(user_id, *roles)`: CIO for grouping, agent runs, view decisions, run
  decisions and research upload; Compliance for releasing research; RM for goal declarations. A wrong role →
  `Forbidden` with the role needed.
- **Not checked:** dismissing news and releasing a restricted-list hold (`src/news/ops.py`) take any user id
  (DEF-03).
- Separation of duties implemented: research releaser ≠ uploader.
- Reads by role: `src/apply/reads.py` (CIO/Compliance/Admin all runs; RM effective/superseded/withdrawn; client
  effective only).

## Rules
The switcher is **not security** ([ADR-0006](../decisions/ADR-0006-the-role-switcher-is-not-security.md)); every
screen with it says “demo”.

## Implementation
`src/control/roles.py`; checks in `src/events`, `src/views/ops.py`, `src/apply`, `src/news/ops.py`,
`src/research`; UI `web/shell.js` (`ROLES`).

## Acceptance and tests
`tests/test_views.py::test_only_the_cio_runs_the_agent_and_decides`;
`tests/test_research.py::test_a_report_waits_for_compliance_and_then_reaches_the_inbox` (an RM cannot upload),
`::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time`;
`tests/test_apply.py::test_a_held_run_is_hidden_from_rms_until_the_cio_makes_it_effective`.

## Limitations
- No authentication (SSO is a bank matter).
- No RM-to-family assignment: the one RM sees every family (Q-17).
- Two-person rules for prompts, models, factor model, thresholds and lists are not built (FEAT-14, Q-15).
- The pre-BRD services (dashboard, statements, declarations, risk, alerts, scenarios, the RM queue) take no
  user id and check no role.

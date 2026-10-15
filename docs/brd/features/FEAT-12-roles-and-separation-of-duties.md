# FEAT-12 — Sign-in, roles and separation of duties

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-RULE-ROLE-01…06, BRD-RULE-SEC-01, BRD-RULE-SEC-02, BRD-RULE-SEC-04, BRD-RULE-SEC-10 |
| Users | Everyone |
| Entry points | The sign-in page (shown to anyone without a session); `GET /api/auth/me`, `POST /api/auth/login`, `POST /api/auth/demo`, `POST /api/auth/logout`, `GET /api/auth/accounts` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Each person signs in as themselves and sees only their own work: a customer their family, an RM the families
assigned to them, the CIO, Compliance and Admin their pages. Each action is done only by the role allowed to do it,
and the steps that need two people get two people.

## Behaviour
- **People** (`src/people/store.py`, owner 2026-10-16): one table of everyone — customers and household members
  (`kind` client), their dependents, and the staff (`data/people/staff.json`, written by `scripts/make_people.py`):
  `cio` Trần Quang Huy, `cio2` Lê Thu Hà, RMs `rm01` Hoàng Hải Yến (C01, C04, C05), `rm02` Ngô Minh Châu (C02),
  `rm03` Trần Quốc Bảo (C03), `compliance` Đỗ Minh Châu, `compliance2` Vũ Hải Nam, `admin`, and five
  specialists. A family's team and its assigned RM (`people.rm_id`) come from the same rows, so “your RM” and the
  RM who signs in are the same person.
- **Accounts and sessions** (`src/people/auth.py`, [ADR-0020](../decisions/ADR-0020-sign-in-with-own-accounts.md)):
  everyone but the specialists and dependents has an account; login by e-mail or id; scrypt-hashed password; a
  signed HttpOnly cookie for 12 hours. A wrong login or password gets one answer, after a short delay, and every
  sign-in is an audit row (`auth.sign_in`). With `MF_DEMO_ACCOUNTS=on` the sign-in page lists the accounts by
  role and opens one with a click.
- **What each person sees**: the shell shows only the signed-in person's role and its pages, their name and
  “Đăng xuất”; an address of another role's page opens their own. A customer has no family picker (their own
  family, the client view always); an RM's picker lists their families; CIO, Compliance and Admin see every family.
- **Checks**: `SignInGate` (`app/web.py`) refuses `/api/*` reads without a session (401), staff routes to
  customers and other families' data to anyone (403); in served runs, a family's data (`fixtures.client`), the
  view (`auth.role_for`), the acting user (`roles.user`: nobody acts in someone else's name) and lists over every
  family (`auth.visible`: search, the review queue, the advisory record, regulation matches, the RM's today).
- News-impact actions call `roles.require(user_id, *roles)`: CIO for grouping, agent runs, view decisions, run
  decisions and research upload; Compliance for releasing research and restricted-list holds; RM for goal
  declarations and approval decisions. A wrong role → `Forbidden` with the role needed.
- Separation of duties: research releaser ≠ uploader; configuration needs a second owner (FEAT-14).
- Reads by role: `src/apply/reads.py` (CIO/Compliance/Admin all runs; RM effective/superseded/withdrawn; client
  effective only).

## Rules
Only a verified session is trusted (BRD-RULE-SEC-01). `MF_AUTH=off` turns the checks off and is used only by the
ordinary test suite. Runs that no request started (scheduled jobs, the engine over every family) are not checked.

## Implementation
`src/people/store.py`, `src/people/auth.py`, `src/control/roles.py`, `src/wealth/fixtures.py` (`client`),
`app/web.py` (`SignInGate`, `/api/auth/*`); the checks in `src/events`, `src/views/ops.py`, `src/apply`,
`src/news/ops.py`, `src/research`, `src/search`, `src/feed`, `src/overview`, `src/copilot`; UI `web/shell.js`,
`web/pages/signin.js`.

## Acceptance and tests
`tests/test_auth.py` (14 tests: accounts, hashing, signed and expiring sessions, login and one answer for any
failure, demo list switch, audit row, 401 without a session, a customer only their family and only the client
view, an RM only their families, lists filtered, nobody acts in someone else's name, unserved runs unchecked);
`tests/test_people.py`; `tests/ui/test_signin.py`; every browser test signs in as the route's role;
`tests/test_views.py::test_only_the_cio_runs_the_agent_and_decides`;
`tests/test_research.py::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time`.

## Limitations
- A refused `POST` run answers 500, not 403 (operonx 1.19 has no exception-to-status mapping); the data is refused.
- The form is the demo's; a bank signs in through SSO (the session and the checks stay).
- Admin signs in and sees configuration, agents and the audit log; the admin screens for sources and data loading
  are BRD_COMPLETION_PLAN F5.

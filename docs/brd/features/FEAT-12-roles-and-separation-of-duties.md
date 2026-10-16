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
  `rm03` Trần Quốc Bảo (C03), `compliance` Đỗ Minh Châu, `compliance2` Vũ Hải Nam, `admin`, `admin2` Đỗ Minh
  Khôi (the second Admin for prompts and models, F4), and five specialists. A family's assigned RM is the
  `rm_assignment` configuration in force (Admin, FEAT-14; version 1 from the seed's teams): “your RM”, the RM who
  signs in, what they may see and act for all follow it (F5). A staff member
  added to the seed later joins a database made before, with an account (`store._top_up`).
- **Accounts and sessions** (`src/people/auth.py`, [ADR-0020](../decisions/ADR-0020-sign-in-with-own-accounts.md)):
  everyone but the dependents has an account (specialists since G8: they approve action recommendations for
  the families whose team they lead, BRD-RULE-ROLE-05); login by e-mail or id; scrypt-hashed password; a
  signed HttpOnly cookie for 12 hours. A wrong login or password gets one answer, after a short delay, and every
  sign-in is an audit row (`auth.sign_in`). With `MF_DEMO_ACCOUNTS=on` the sign-in page lists the accounts by
  role and opens one with a click.
- **What each person sees**: the shell shows only the signed-in person's role and its pages, their name and
  “Đăng xuất”; an address of another role's page opens their own. A customer has no family picker (their own
  family, the client view always); an RM's picker lists their families; CIO, Compliance and Admin see every family.
- **Checks**: `SignInGate` (`app/web.py`) refuses `/api/*` reads without a session (401), a read to a role its
  path does not allow (`ROUTE_ROLES`: e.g. the inbox and draft views only to CIO, Compliance and Admin, the audit
  log to Compliance and Admin, market data to CIO and Admin) and other families' data to anyone (403); in served runs, a family's data (`fixtures.client`), the
  view (`auth.role_for`), the acting user (`roles.user`: nobody acts in someone else's name) and lists over every
  family (`auth.visible`: search, the review queue, the advisory record, regulation matches, the RM's today).
  A served action refused answers 403 with the reason, not signed in 401 (operonx 1.27 `http_status` on
  `Forbidden` and `NotSignedIn`). Uploading a statement, declaring assets and proposing a plan check the family;
  an RM decides review items only for their families; fetching the news now is the CIO's (F5).
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
`tests/test_access.py` (every served read and action as seven people — two families, an assigned and an
unassigned RM, CIO, Compliance, Admin — against the matrix written in the test; a route not in the matrix fails;
the RM reassignment); `tests/test_system.py` (Hệ thống and the history load); `tests/test_people.py`;
`tests/ui/test_signin.py`; every browser test signs in as the route's role;
`tests/test_views.py::test_only_the_cio_runs_the_agent_and_decides`;
`tests/test_research.py::test_the_uploader_cannot_release_and_nothing_goes_out_before_its_time`.

## Limitations
- The form is the demo's; a bank signs in through SSO (the session and the checks stay).
- Admin's screen is Hệ thống ([SCR-ADM-01](../ux/screens/admin.md#scr-adm-01--hệ-thống-system)): jobs, feeds,
  agents, the audit chain, history loads and accounts; sources and the RM assignment are edited in Cấu hình. It
  has no password form: on the public demo anyone can sign in as Admin (`scripts/set_password.py` sets one).
- A served action whose input is wrong still answers 500 in most places (a `ValueError`); only the history load
  answers 400 (`control.errors.BadRequest`).

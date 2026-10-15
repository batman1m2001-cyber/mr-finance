# ADR-0020 — Everyone signs in with their own account; the role switcher is gone

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** BRD §13.1 (BRD-RULE-SEC-01, SEC-02, ROLE-02); owner, 2026-10-16 (“if it's not [a BRD requirement],
  then do the authen login”); docs/BRD_COMPLETION_PLAN.md F1
- **Supersedes:** [ADR-0006](ADR-0006-the-role-switcher-is-not-security.md)

## Context

The demo showed every role side by side behind a switcher (ADR-0006). The BRD does not ask for that: it asks that
only a verified sign-in be trusted (SEC-01), that an RM open only their own families (ROLE-02) and that every API
check the role (SEC-02). The people — customers, household members, RMs, CIOs, Compliance, Admin and the
specialists — are now rows of one table (`src/people/store.py`), so an account can belong to a person.

## Decision

- **Accounts** (`src/people/auth.py`): every customer, household member, RM, CIO, Compliance officer and Admin has
  one; specialists do not act in the app. Login is the e-mail (or the id); the password is a salted scrypt hash.
  Seeds get `MF_DEMO_PASSWORD` when it is set, else no password until `set_password`.
- **Session**: an HttpOnly, SameSite=Lax cookie (Secure on https) holding the person's id and a 12-hour expiry,
  signed with HMAC-SHA256 (`MF_SESSION_SECRET`, else a key generated once and kept in the state file).
- **What a person sees**: the shell shows only their role's pages. A customer sees their own family (a household
  member: the family they belong to) and always the client view; an RM sees the families assigned to them
  (`people.rm_id`); CIO, Compliance and Admin see every family for their work.
- **Where it is checked**: `SignInGate` (app/web.py) answers 401 to any `/api/*` read without a session, 403 to a
  customer on a staff route and to anyone opening a family they may not see. Inside served runs,
  `fixtures.client` refuses a family's data (`auth.require_client`), `roles.user` refuses an action in someone
  else's name, `auth.role_for` sets the view from the person, and lists over every family keep only theirs
  (`auth.visible`). Runs that no request started (scheduled jobs, the engine, direct runs) are not checked.
- **Demo accounts**: `MF_DEMO_ACCOUNTS=on` lists the accounts on the sign-in page, one click each. It is for the
  public demo; a bank deployment turns it off and signs in through its SSO instead of the form.

## Consequences

- SEC-01 and ROLE-02 are met in the demo's form; Q-17 is closed.
- A refused served run (`POST /api/…`) answers 500, not 403: operonx 1.19 maps no exception to a status. The data
  is still refused; a status mapping is an upstream follow-up.
- The ordinary test suite runs with `MF_AUTH=off`; `tests/test_auth.py` and the browser tests run with sign-in on.

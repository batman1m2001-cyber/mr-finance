# ADR-0006 — The role switcher is a demo, not security

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** docs/NEWS_IMPACT_PLAN.md A3

## Context

The BRD requires a verified sign-in and role checks on every API (§13.1). The demo has no identity provider.

## Decision

- The UI's role switcher sends a demo user id (`cio`, `cio2`, `rm01`, `compliance`, `compliance2`, `admin`) with each action; the server checks that user's role and separation of duties (`src/control/roles.py`).
- Every screen showing the switcher says “demo”; the footer says it is not a security mechanism.

## Consequences

- Role and SoD logic is real and tested; authentication is not. A bank deployment replaces the id with an SSO identity (BRD-RULE-SEC-01: `out_of_scope_demo`).

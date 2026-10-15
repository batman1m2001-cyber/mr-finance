# ADR-0013 — Wrap the legacy pages in the new shell instead of rewriting them

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** docs/NEWS_IMPACT_PLAN.md §5, §8

## Context

The redesign (U1–U2) added role-based navigation and new pages. The pre-BRD pages (`web/app.js`, 8 tabs) work and carry many capabilities.

## Decision

- `web/shell.js` routes per role (`#/<role>/<page>[/<sub>][/<param>]`). A legacy page is shown by `window.Legacy.showTab(...)`; new pages are ES modules in `web/pages/` rendered into `#page-new`.
- New CSS classes are scoped to `:is(#page-new, .drawer)` because the legacy CSS already uses `.hero`, `.badge`, `.btn`, `.legend`.
- A test checks every legacy section is still present.

## Consequences

- Two visual generations coexist; known defects of the legacy pages stay until they are redesigned (DEF-01).

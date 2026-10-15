# ADR-0003 — Keep the capabilities that predate the BRD

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** SRC-02; docs/PLAN.md; kit rule KIT-DOC-02

## Context

Consolidation, the dashboard, statement reading, chat declarations, the risk test, life scenarios and stress tests, policy-cost alerts, the RM approval queue, goals planning, house views and the advisory pages were built from the original brief and PR #13 before the BRD arrived. The BRD covers a different module and even calls Open API and statements out of its scope (§3).

## Decision

- Every pre-BRD capability is kept and documented as an **existing capability** (Layer A: [brief_requirements.md](../requirements/brief_requirements.md); Layer B: FEAT-20…FEAT-28).
- The redesign wrapped their pages in the new shell without removing any section (ADR-0013); since 2026-10-16 each is a rebuilt module page with every section kept (ADR-0019, `tests/test_web.py::test_every_page_is_a_module_page`).
- Overlaps with the BRD are recorded as conflicts (Q-03, Q-04), not resolved by deleting either side.

## Consequences

- Two impact methods coexist (engine and point rules); ADR-0007 limits the overlap.
- Removing any of these capabilities later requires a new ADR and a changelog entry.

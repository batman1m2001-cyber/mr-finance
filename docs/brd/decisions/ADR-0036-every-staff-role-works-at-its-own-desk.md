# ADR-0036 — Every staff role works at its own desk, in the Customer workspace's frame

- **Status:** accepted for the experiment (branch `exp/graph-workspace`); supersedes ADR-0035 §1 ("RM and the staff
  roles keep the page shell") for the staff roles
- **Date:** 2026-10-18
- **Sources:** OWN-MR-01…12; FEAT-41; docs/MULTI_ROLE_UX_PLAN.md

## Context

The owner asks for the Customer's redesign to reach CIO, RM, Admin and Expert, each purpose-built, without losing a
capability, keeping each role's agents working and giving each its own assistant. Today the staff roles have a row
of tabs (the CIO thirteen, overflowing at 1440 px) whose first tab is a list, and a floating assistant with a thin
tool set. The Customer's centre — a radial graph around the family's net worth — has no meaning for a CIO or an
Admin, and the request says not to force every role into it.

## Decision

1. **The frame is shared, the centre is not.** Every staff role gets the rail, the dock (assistant · inspector) and
   sheets of FEAT-40; each role's centre is built for its job: the CIO's pipeline of decisions, the RM's book of
   families, Admin's system map, the Expert's review desk with evidence, Compliance's controls.
2. **Pages become sheets at their old addresses.** No menu id changes; `#/<role>` (and `/ban`) is the desk; every
   page module renders unchanged in a sheet. The rail only groups pages.
3. **One composed, read-only endpoint per desk,** `GET /api/desk`, role from the session, built from the existing
   stores and filters; the role's assistant reads the same composition through new read tools, so the screen and
   the assistant say the same numbers.
4. **No new permission and no new write.** A desk acts only through existing writes (the specialist's decision,
   the RM's contact), which keep their server checks.
5. **The assistant docks for every role** (streaming door, progress list, live highlight), as for the Customer.

## Consequences

The staff shells change shape; their pages do not. Tests that open staff pages find them inside a sheet. The
Customer workspace changes only by the extraction of the dock's divider into a shared module. If the experiment is
not taken, the branch is dropped.

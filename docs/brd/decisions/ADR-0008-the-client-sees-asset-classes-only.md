# ADR-0008 — The client sees effective results at asset-class level only

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** docs/NEWS_IMPACT_PLAN.md A7; BRD §14

## Context

BRD §14 flow 2: family updates carry impact by asset group and goal, with no ticker names and no action words, after CIO approval and RM pre-review. The product has a client role.

## Decision

- `src/apply/reads.py::family_impact(role="client")` returns only EFFECTIVE runs, by asset class, with the event's type label instead of its headline (a headline can name a company), the AI label, the approver and “không phải khuyến nghị”.
- The trace (“Cách tính”, FR-406) names holdings, so it is staff-only.

## Consequences

- NFR-11's “every number has cách tính” is not met for the client (Q-14).

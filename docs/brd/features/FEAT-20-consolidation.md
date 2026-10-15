# FEAT-20 — Consolidation: every source, one holdings list

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-DATA-01…05; BRD-RULE-DATA-01 (trust labels) |
| Users | Client, RM (through every picture); the engine's snapshot (FEAT-08) reads the same holdings |
| Entry points | No screen of its own: under [SCR-CL-02 Tài sản](../ux/screens/client.md#scr-cl-02--tài-sản-holdings) and [SCR-CL-01](../ux/screens/client.md#scr-cl-01--tổng-quan-overview); graph `consolidate_flow` (a subgraph of the dashboard, alerts, risk and scenario graphs) |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Purpose
One picture of what a client (or their household) holds, wherever it is, each item labelled by how much we can
trust it. Every other picture starts from this one list ([ADR-0015](../decisions/ADR-0015-decisions-of-the-first-build-plan.md) D9).

## Behaviour (`consolidate_flow(client_id, scope)`)
1. `household` — who is in the picture: the client; with `scope="family"`, the members who **consented**
   (C02's spouse did not, so is left out).
2. The connectors run in parallel: **tier 1** `techcombank` (accounts, cards, loans, transactions),
   `tcbs` (stocks, bonds), `techcom_capital` (funds), `onehousing` (properties); **tier 2** `open_api` (other banks,
   only what the client consented to share) and `statements` (files read by FEAT-22); **tier 3** `declared`
   (fixtures' declared assets + what the chat recorded, FEAT-23).
3. `merge_holdings` — one holding shape (key, class, name, value, cost, bought date, source, tier, trust
   `verified`/`statement`/`declared`), duplicates removed, every source counted; transactions kept for the
   cash-flow calendar.
Valuation at the demo market (2026-10-09) is in `src/wealth/valuation.py`.

## Implementation
`src/consolidate/{graph,ops}.py`, `src/wealth/{fixtures,valuation,store}.py`.

## Acceptance and tests
`tests/test_consolidate.py` (5 tests: every tier, the spouse in family view, consent, the merge, client additions);
`tests/test_wealth.py::test_open_api_reads_only_what_the_client_consented_to`, `::test_every_client_fixture_values_without_a_gap`.

## Limitations
All sources are mock fixtures ([ADR-0005](../decisions/ADR-0005-mock-clients-and-prices-public-news.md)); the
BRD puts outside-TCB connections out of its own scope (Q-04).

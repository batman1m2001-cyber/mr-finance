# ADR-0015 — Decisions of the first build plan (D1–D9)

- **Status:** accepted
- **Date:** 2026-10-09
- **Sources:** docs/PLAN.md §1

## Context

The first plan (docs/PLAN.md §1) fixed nine decisions for the brief's product.

## Decision

Recorded there, summarised here so they are not lost:
- **D1** mock data, real logic; **D2** AI where the brief says AI, with a rule fallback (`MF_AI=on|off|auto`); **D3** the risk test is rules, not a model; **D4** advice is a simulation until an RM approves it; **D5** money in VND integers, UI in Vietnamese, code and docs in English; **D6** state in SQLite (`data/state.db`, gitignored); **D7** one Application, one port (8030); **D8** policy facts are dated fixtures with a status and a source line; **D9** `consolidate_flow` is the one graph features share.

## Consequences

- They still hold. D4 is the pre-BRD form of the BRD's human gates; D5 is refined by ADR-0011.

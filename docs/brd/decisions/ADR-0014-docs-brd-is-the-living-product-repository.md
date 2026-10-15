# ADR-0014 — docs/brd is the living product knowledge repository

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** The owner's request of 2026-10-15

## Context

Requirements, behaviour, UI and decisions were spread over a brief, a BRD outside git, three plans and the code. The owner asked for one permanent, layered, traceable repository.

## Decision

- `docs/brd/` holds three layers (requirements, features, UX) plus architecture, decisions, testing, assets and sources, with one traceability matrix as the only place a status is stated.
- Plans stay in `docs/` as history; once built, behaviour is documented here.
- `scripts/check_brd_docs.py`, run by `tests/test_brd_docs.py`, checks links, IDs, coverage of the BRD's 61 codes, cited tests and the kit copies' hashes.
- `AGENTS.md` and `README.md` point here so coding assistants find it first.

## Consequences

- Every meaningful change updates the affected documents ([MAINTAINING.md](../MAINTAINING.md)); the suite fails if a cited test disappears or a link breaks.

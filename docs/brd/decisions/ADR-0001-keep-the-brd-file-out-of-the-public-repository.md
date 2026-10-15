# ADR-0001 — Keep the BRD file out of the public repository

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** SRC-01; `.git/info/exclude`; docs/NEWS_IMPACT_PLAN.md §0–§2

## Context

The repository is public. The BRD `.docx` (SRC-01) was never committed: it is listed in `.git/info/exclude`, and the project's standing rule is to commit no Techcombank material. The BRD calls itself personal research, not Techcombank's view, and carries no confidentiality mark; its five figures are part of it.

## Decision

- The `.docx` and its embedded figures stay out of git. They are identified by local path and SHA-256 in [`sources/README.md`](../sources/README.md) and [`requirements/original_brd_reference.md`](../requirements/original_brd_reference.md).
- Requirements are extracted as text, with the BRD's Vietnamese wording quoted per requirement, so the repository is usable without the file.
- The figures are redrawn by us as Mermaid diagrams where they carry requirements, labelled as our redrawing.
- `scripts/check_brd_docs.py --brd <path>` checks the hash and that every BRD code is extracted.

## Consequences

- Anyone without the file can still read every requirement and its source location; they cannot see the original layout or figures.
- If the owner decides the BRD may be published, commit it under `docs/brd/sources/` and update ADR-0001 (superseded), not the extractions.
- Quoting the requirement texts in a public repository is itself a disclosure; it follows the existing practice of `docs/NEWS_IMPACT_PLAN.md` and is flagged to the owner in the change that introduced this repository.

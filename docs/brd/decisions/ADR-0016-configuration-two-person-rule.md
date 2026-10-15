# ADR-0016 — Configuration is versioned; two people for the factor model, thresholds and restricted list

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** BRD §6.7 FR-701, §13.1 (sentence and ownership table), F14; Q-15

## Context

FR-701 asks for versioned, owned configuration changed by proposal then approval. §13.1's sentence asks for two
people for prompts, AI models, the factor model, alert thresholds and the restricted list; its ownership table
says two people only for prompts and AI models. The BRD's own change record F14 says the factor model, thresholds
and restricted list *were changed* to need two people.

## Decision

- Follow the sentence and F14 (the later and stricter reading): two people — proposer ≠ approver, both of the
  owner's role — for the factor model (CIO), alert thresholds (CIO) and the restricted list (Compliance); one
  person may propose and approve the news sources (Admin).
- Version 1 of each kind is the shipped file; later versions live in `config_versions`; every step is audited;
  the engine, the news gates and the post-check read the version in force; a run freezes its factor model and
  thresholds in its snapshot, so a recompute uses them.
- Prompts and AI models stay code and environment for now (RULE-AI-02 open).

## Consequences

- Stricter than the table: compliant with either reading. Q-15 is resolved for the demo; Compliance can relax it.
- The demo has two users per role for CIO and Compliance (`cio2`, `compliance2`) to make the second person real.

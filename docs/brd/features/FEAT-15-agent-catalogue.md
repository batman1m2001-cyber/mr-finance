# FEAT-15 — Agent catalogue

| | |
|---|---|
| Type | BRD capability — **partially built** |
| Requirements | BRD-FR-703, BRD-RULE-AI-01 |
| Users | Compliance, Admin, CIO |
| Entry points | `GET /api/agents`; the mode badge on the CIO's view page |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## What exists
`GET /api/agents` returns the mode an agent run would use now (`live` or `mock`), the two models (or
`mock`/`rules`), the prompt version, and the demo users. Every agent run and its nodes are stored (FEAT-04).

## What is missing (BRD FR-703)
A catalogue entry per agent — CIO agent, challenger, policy agent, internal explanation — with purpose, owner,
risk level, AI model, latest run and open-source references (BRD §8 table gives the content). No screen.

## Plan
News plan phase N5 (optional), not started.

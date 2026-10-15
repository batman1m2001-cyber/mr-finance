# ADR-0002 — Implement the BRD on operonx, not on the BRD's stack

- **Status:** accepted
- **Date:** 2026-10-15
- **Sources:** docs/NEWS_IMPACT_PLAN.md §0, §4; Q-01

## Context

The BRD describes its author's demo on TypeScript, Hono, Cloudflare Workers/D1, React, LangGraph (§12.1). This product was already a Python operonx application (docs/PLAN.md) and the owner confirmed it must stay on operonx.

## Decision

- The BRD's requirements are implemented in Python as operonx graphs, services and jobs (`app/main.py`), with SQLite state (`data/state.db`) and a no-build web UI.
- The BRD's stack-specific statements (Zod, decimal.js, D1, Workers, LangGraph, Cloudflare Access, 28 tables, ~80 endpoints) are architecture notes, not requirements. Where they express a rule, the rule is kept (schema validation before saving; append-only log with triggers; idempotency keys).
- The BRD's “Demo: Đã có” column is never used as our status.

## Consequences

- Requirements map to operonx equivalents (e.g. LangGraph's 8-node graph → `cio_agent_flow`; Zod → `src/views/schema.py`; Cloudflare cron → `Job(schedule=every="10m")`).
- Some BRD tables have no counterpart yet (config_versions, external_outputs, policy_documents, goal_impacts); each is a gap in the matrix.

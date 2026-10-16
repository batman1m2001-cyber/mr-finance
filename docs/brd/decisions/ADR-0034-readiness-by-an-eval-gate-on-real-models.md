# ADR-0034 — Readiness is an eval gate on real models, with measured costs

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** OWN-AS-23, OWN-AS-24; brief §5; docs/ASSISTANT_PLAN.md A-D9

## Context

The brief forbids claiming production readiness on mocks and asks for tracked quality, reliability, latency and cost.
The live demo already runs real models through OpenRouter.

## Decision

- `evals/assistant/` holds realistic Vietnamese conversations per role with expectations (tools called, facts in the
  answer, citations, refusals, memory effects, no leaked data), run against the real models by
  `scripts/eval_assistant.py` — not part of the ordinary test run (it costs money), recorded per run.
- Metrics: answer accuracy, grounding (claims backed by a tool result or source), citation presence, tool success,
  correct refusals, leakage (zero tolerated), injection resistance, latency p50/p95, tokens and cost per conversation,
  background cost per day.
- A gate (thresholds in the eval file) decides readiness; the readiness report states the numbers, the failures
  fixed, those left, and the services not available.
- The ordinary suite keeps deterministic tests (scripted models) for the mechanics: permissions, confirmations,
  verification, isolation, deletion, persistence, concurrency.

## Consequences

Each eval run spends a few dollars; prompt or model changes must pass the gate before shipping.

# ADR-0012 — The Copilot routes; it never reads client data

- **Status:** accepted; implemented 2026-10-16 (FEAT-32), stricter on one point: no entity id reaches the model;
  amended by ADR-0026 (the assistant may read client data where `client_ai` allows; this rule is its `off` mode)
- **Date:** 2026-10-15
- **Sources:** docs/REDESIGN_KIT_PLAN.md D1–D3; Q-06

## Context

The redesign kit asks for an assistant that answers from authorised data and runs tasks. BR-11, §7.1, §14 and NFR-08 forbid client data reaching an AI provider.

## Decision

- The language model sees only a scrubbed question, the page's route and entity ids, and the tool catalogue; it returns a tool call. Our code runs the tool and writes the answer from deterministic templates.
- A scrubber removes digits, amounts, account and ticker codes and every known client, spouse and dependent name before the router; a test asserts none reaches the prompt.
- Actions only through existing served graphs, with the active user's id (server role and SoD checks apply), and an explicit confirm step for any write; answers report the endpoint's real result.
- Default router: keyword (mock, labelled); live router: `llm:copilot`.

## Consequences

- A real assistant without breaking the barrier; answers are template-shaped, not free prose.

# ADR-0026 — The assistant's model reads client data only where `client_ai` allows it

- **Status:** accepted (amends ADR-0012)
- **Date:** 2026-10-16
- **Sources:** OWN-AS-03, OWN-AS-09; BRD-BR-11, BRD-NFR-08; ADR-0012, ADR-0018, ADR-0023; docs/ASSISTANT_PLAN.md A-D1

## Context

The owner wants the assistant to answer about the person's own financial data in its own words, run several tools
and explain. ADR-0012 kept the Copilot's model blind: it saw only the scrubbed question and chose one tool; answers
came from templates. The BRD forbids client data reaching an AI provider the bank has not approved (BR-11, NFR-08),
and G2 made that a configuration (`client_ai`: `demo`, `onprem`, `off`) enforced at every `llm:` call
(`control/barrier.py`).

## Decision

- The assistant's model is an ordinary `llm:` resource call, so the barrier applies to it with no new path.
- **`demo`** (the public demo, mock clients, owner decision ADR-0018) and **`onprem`** (the bank's own model on an
  allowed host): the model reads tool results and writes the answer, citing them.
- **`off`**: *template mode*. The model sees the scrubbed message and each tool's status only, may chain tools, and
  the answer is the tools' own templated texts in order — ADR-0012's guarantee, now multi-step.
- Whatever the mode, the model never receives another person's data: tools resolve the owner on the server.

## Consequences

The bank's rule holds by configuration, as for the client steps. Answers in `off` mode stay templated (accurate,
less fluent). Tests check, per mode, what text reached the model.

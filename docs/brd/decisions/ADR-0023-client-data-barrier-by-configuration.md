# ADR-0023 — The client-data barrier is one guard on every model call, set by configuration

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** BRD §14, §15 (BRD-NFR-08, BRD-BR-11); docs/BRD_REMAINING_PLAN.md G-D2, G2
- **Amends:** [ADR-0018](ADR-0018-owner-decisions-public-quotes-and-ai-in-the-demo.md) (the demo keeps its
  behaviour as one setting among three)

## Context

ADR-0018 let the demo send client text (an uploaded statement, a chat message) to the configured model. A bank
cannot run that way: NFR-08 says client data never reaches an AI provider. The model is called from several places —
`LLMOp` (statements), the declaring agent, the CIO agent and challenger (`views/agents.call_model`), the newsletter
and policy agents, the Copilot's router — so a check in each would be one check missed.

## Decision

- **`client_ai` is configuration** (Cấu hình › “AI với dữ liệu khách hàng”; owner Admin, two people):
  - `demo` — today's behaviour; the public demo stays here.
  - `onprem` — the statement reader and the declaring chat call `llm:onprem`, the bank's own model; a model is inside
    only when its address's host is on `onprem_hosts`. `llm:onprem` off the list is refused every call, and the two
    steps take their rules.
  - `off` — the two steps take their rules; no model hears from a client.
- **One guard on every `llm:` resource** (`control/barrier.py::check`, registered with operonx's
  `ResourceHub.guard("llm:", …)`, operonx 1.28.0, at app start). In `onprem` and `off`, a call bound for a host not on
  the list and carrying any client identifier — a client's or household member's id or full name, a dependent's
  name (seeded or declared in the chat), any account, card, loan or property number in their source systems; names
  with or without accents — raises `ClientDataRefused` (403) before anything is sent. The refusal is logged and
  audited (`ai.refused`) without the identifiers.
- A model client built outside the hub (`views/agents._llm`, another model name on the same resource) is guarded the
  same way.
- `/healthz` reports the setting (`client_text_off_ai`).

## Consequences

- NFR-08's “never sent to an AI provider” is a setting the bank switches on, proven at the wire by
  `tests/test_barrier.py`: every model resource points at a recording server; in `off` the client steps send nothing
  and named client data is refused on every path; in `onprem` only the bank's host is reached.
- The identifier check is the second line, not the first: in `off` and `onprem` the client steps never call an
  outside model at all. A statement with no name in it is still client data, so the routing, not the guard, keeps
  it in.
- Storage in Vietnam and the provider's contract (no storing, no training) stay bank matters.

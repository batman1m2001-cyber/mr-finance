# ADR-0018 — Owner decisions: BRD quotes stay public; the demo may send client text to the model

- **Status:** accepted
- **Date:** 2026-10-16
- **Sources:** owner decisions D-01 and D-03 (`docs/TO_DISCUSS.md`), 2026-10-16: “keep them public and go
  straight to model, there is no private here”

## Context

D-01: the BRD's requirement texts are quoted verbatim in this public repository (ADR-0001 keeps only the `.docx`
out). D-03: when AI is on, the pre-BRD statement reader (FEAT-22) and declaration chat (FEAT-23) send client text to
the model; BRD-BR-11 / NFR-08 forbid client data reaching an AI provider. The live demo has AI on.

## Decision

- The quotes stay in the public repository. The `.docx` itself stays out (ADR-0001 unchanged).
- The demo keeps AI on for the statement reader and the chat: the clients are mock, nothing is private.

## Consequences

- NFR-08 stays `partially_implemented`: a bank deployment must run those two steps on an on-premise model or on
  their rule paths; `/healthz` keeps showing `client_text_off_ai` as off.
- The news-impact barrier (BR-11, ADR-0009) is unchanged: the CIO agent and challenger still receive no client data.

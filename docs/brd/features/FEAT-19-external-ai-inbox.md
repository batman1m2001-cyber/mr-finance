# FEAT-19 — External AI zone and signed inbox

| | |
|---|---|
| Type | BRD capability — **not built** (demo form in place) |
| Requirements | BRD-FR-307 (inbox mode), BRD-RULE-ZONE-01…03, BRD-RULE-ZONE-06, BRD-RULE-LC-04, BRD-RULE-SEC-07 |
| Users | Admin (operations), CIO |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## What the BRD asks
AI runs outside the bank with its own database and pushes signed result packages into a write-only inbox
(`external_outputs`: READY → PROCESSING → IMPORTED | REJECTED), imported every 10 minutes through the same
checks as live mode; unsigned records refused when the key is set.

## What exists instead
One process; the barrier is enforced by the agent graphs' inputs and tested
([ADR-0009](../decisions/ADR-0009-ai-barrier-by-graph-inputs-in-one-process.md)). Live and mock modes exist; the
inbox mode does not.

## Plan
News plan phase N5 (“HMAC inbox”), not started.

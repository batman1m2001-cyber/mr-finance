# ADR-0009 — The AI barrier is enforced by graph inputs, in one process

- **Status:** superseded in part by [ADR-0022](ADR-0022-the-ai-zone-is-a-second-process.md) (the zone and the inbox are built; the graph-input barrier stays)
- **Date:** 2026-10-15
- **Sources:** docs/NEWS_IMPACT_PLAN.md A4; Q-23

## Context

BRD §7.1 puts AI in a separate zone with its own database and a signed write-only inbox. The demo is one process.

## Decision

- The agent ops take only the event's news, released research, the factor catalogue and the instrument catalogue as inputs; a test asserts that no client name, account or balance reaches any prompt (`tests/test_views.py::test_live_mode_uses_two_models_and_no_client_data_reaches_them`).
- Data in prompts is wrapped in DỮ_LIỆU … HẾT_DỮ_LIỆU.
- The signed inbox (FR-307 inbox mode, external_outputs) is planned, not built.

## Consequences

- The barrier is a tested code property, not a network one (the BRD itself says the same of its demo, §7.1 “Trạng thái demo”).

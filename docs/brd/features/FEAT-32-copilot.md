# FEAT-32 — OneWealth Copilot

| | |
|---|---|
| Type | Proposed extension (redesign kit), approved for planning 2026-10-15 — **not built** |
| Requirements | KIT-COPILOT-01…06; must keep BRD-BR-11, BRD-NFR-08, BRD-RULE-ZONE-04 |
| Users | Every role |
| Plan | [docs/REDESIGN_KIT_PLAN.md](../../REDESIGN_KIT_PLAN.md) phase **K5**, decisions D1–D3; [ADR-0012](../decisions/ADR-0012-the-copilot-routes-and-never-reads-client-data.md) |
| Status | see [traceability](../requirements/requirements_traceability.md) §4 |

## Intended behaviour
`src/copilot`: a typed tool catalogue over the existing reads and served graphs (each tool: inputs, roles,
read/write); a scrubber; routers (keyword mock, `llm:copilot`); answer templates; served on `POST /api/copilot`.
The model sees the scrubbed question, route and entity ids and the catalogue; it returns a tool call; our code runs
it with the active user's id and writes the answer from templates. Writes need an explicit confirm step and
report the endpoint's real result or error. UI: a floating button, a side drawer, page context, follow-ups,
progress and error states; the conversation lives in the page session.

## Acceptance (plan gate)
Barrier test (no fixture name or number in any router prompt); a client cannot run a CIO tool; no write without
confirm; a failing tool reported as failed; one recorded live run.

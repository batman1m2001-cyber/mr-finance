# FEAT-23 — Declaring assets by chat

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-DATA-03 |
| Users | Client (Tài sản → Bổ sung tài sản) |
| Entry points | [SCR-CL-02](../ux/screens/client.md#scr-cl-02--tài-sản-holdings); `POST /api/declare {client_id, message, session_id}` |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Behaviour (`declare_flow`)
One chat turn. With AI on, an operonx-agents `Agent` with six tools writes to the client's profile:
`declare_property`, `declare_gold`, `declare_holding`, `declare_loan`, `declare_dependent`, `declare_income`
(a call identical to one already made in the same run is answered “already recorded”). Without AI, or when the
agent cannot answer, a rule reader handles the brief's sentences. The reply lists what was recorded; land with a
size is valued by its area.

## Implementation
`src/declare/{graph,ops,tools,_rules}.py`.

## Acceptance and tests
`tests/test_declare.py` (7 tests, incl. `::test_the_same_call_twice_in_one_turn_is_recorded_once`).

## Limitations
As FEAT-22: client data reaches the model when AI is on (bank deployment: in-bank model only).

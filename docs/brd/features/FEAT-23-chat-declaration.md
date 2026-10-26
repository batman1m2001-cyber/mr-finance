# FEAT-23 — Declaring assets by chat

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-DATA-03 |
| Users | Client (Tài sản → Bổ sung tài sản) |
| Entry points | [SCR-CL-02](../ux/screens/client.md#scr-cl-02--tài-sản-holdings); `POST /api/declare {client_id, message, session_id}`; `POST /api/declare/stream` (the same turn as SSE, what the page uses) |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Behaviour (`declare_flow`, `declare_stream_flow`)
One chat turn. With AI on, an operonx-agents `Agent` (`src/declare/agent.py`) writes to the client's profile with
`declare_property`, `declare_gold`, `declare_holding`, `declare_loan`, `declare_dependent`, `declare_income`
(a call identical to one already made in the same run is answered “already recorded”). Without AI, or when the
agent fails before writing, a rule reader handles the brief's sentences.

- **Streamed** (2026-10-26). The page posts to `/api/declare/stream`: `start`, a `step` per tool ("Đang ghi nhà
  đất"), the agent's words as `text`, a `form` when it asks back, then `answer` with the same turn as the JSON door.
  Only the chat bubble and the book redraw; the page is not reloaded (a statement upload no longer reloads it either).
- **Short and human.** One or two sentences in "em"/"anh/chị" naming what was recorded with its main number; no
  restated profile, no markdown.
- **Asks back little.** Only what an item cannot be valued without (a house with no value or size, a loan with no
  balance); optional details are not asked. At most one question or one form a turn, never asked again. Several
  numbers → `hoi_them` shows a form (≤4 fields: money, number, text, choice); one choice → chips. The client's answer
  fills in the item already recorded under the same name instead of adding a second.
- **The book's value.** Land or a home with a size in a priced area is valued by the area's price (as before); the
  tool tells the agent that figure and the reply says it when it differs from what the client said.

## Implementation
`src/declare/{graph,agent,ops,tools,_rules}.py`; the chat in `web/pages/holdings.js`.

## Acceptance and tests
`tests/test_declare.py` (7 tests, incl. `::test_the_same_call_twice_in_one_turn_is_recorded_once`);
`tests/test_declare_stream.py` (7 tests: the stream, the form, the rules fallbacks, the fill-in, the book's value).

## Limitations
As FEAT-22: in `demo` (the public demo, ADR-0018) client text reaches the configured model when AI is on; a bank sets
`client_ai` to `onprem` (the agent runs on `llm:onprem`) or `off` (the rules answer) — ADR-0023, `tests/test_barrier.py`.

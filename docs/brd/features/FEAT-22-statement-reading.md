# FEAT-22 — Reading an uploaded statement

| | |
|---|---|
| Type | Existing capability (original brief, docs/PLAN.md); outside the BRD — kept by [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md) |
| Requirements | BRIEF-DATA-02 |
| Users | Client (Tài sản → Tải sao kê) |
| Entry points | [SCR-CL-02](../ux/screens/client.md#scr-cl-02--tài-sản-holdings); `POST /api/statement {client_id, filename, content(base64)}`; eval `uv run operonx run statement_reading` |
| Status | see [traceability](../requirements/requirements_traceability.md) §3 |

## Behaviour (`statement_flow`)
`read_file` (PDF text, Excel/CSV rows) → AI on? (`MF_AI=on`, or `auto` with `LLM_API_KEY`) → `model_read` with
`llm:assistant`, else `rule_read` (the known layouts: VPS, SSI, Vietcombank) → if the model fails or returns
nothing usable, the rules step in → `pick_items` → `save_holdings` as `statement` holdings (reading the same
file again replaces it). Deposits keep their rate and maturity; numbers are read in every Vietnamese spelling.

## Implementation
`src/statements/{graph,ops,_parse,checks}.py`; samples `data/samples/` (vps_C01.csv, ssi_C05.xlsx, vcb_C04.pdf,
mbs_C02.csv, hsc_note.txt).

## Acceptance and tests
`tests/test_statements.py` (7 tests); eval `statement_reading` (gate 0.8): rules alone 4/5; a real model
(OpenRouter Haiku 5.5) 5/5 on 2026-10-10 (docs/PLAN.md).

## Limitations
This is client data (BRD NFR-08). The `client_ai` setting decides where it may go (ADR-0023): `demo` (the public
demo) sends the mock statement to the configured model when AI is on; `onprem` reads it with `llm:onprem`, the
bank's own model; `off` reads it with the rules. `tests/test_barrier.py` proves it at the wire.

## The assistant's door (2026-10-26)
A statement can also be given to the assistant (FEAT-42): a table file goes through this same reader; a photo or a
scanned PDF (text under 50 characters) is read by one vision call on the client model, and its holdings are saved by
`save_holdings` behind Xác nhận (`them_tu_tep`). Before this, a scan gave no item.

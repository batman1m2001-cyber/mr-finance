# FEAT-09 — “Cách tính”: from a number back to the news

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-12, BRD-FR-406, BRD-NFR-11, BRD-RULE-SEC-09 |
| Users | CIO, RM, Compliance (staff only) |
| Entry points | “Cách tính” on [SCR-RM-02](../ux/screens/rm.md#scr-rm-02--tác-động-tin-family-impact-staff) → drawer [SCR-RM-03](../ux/screens/rm.md#scr-rm-03--cách-tính-trace-drawer); `GET /api/trace/{run_id}/{family_id}?key=&horizon=` |
| Status | see [traceability](../requirements/requirements_traceability.md) |

## Purpose
Show where a family's number comes from, end to end, so nobody has to trust it blindly.

## Behaviour
From one number (a family's 3-month expected change, or one holding's), the trace returns, in order:
the number and its band → the formula (a fixed sentence) → the holdings behind it (value, loadings, method,
“theo mô hình” label) → each branch (probability, core shocks, the factor moves the engine propagated, the
family's change in that branch) → the approved view (who, when, why; the challenger's findings and the CIO's
answers) → the event → the news items (outlet, link, published time) → the snapshot (hash, price date, model
version and hash, engine version).

## Rules
Staff only: it names holdings and headlines, which client content may not (flow 2,
[ADR-0008](../decisions/ADR-0008-the-client-sees-asset-classes-only.md)). The client sees the formula sentence
and the asset-class breakdown instead (Q-14).

## Implementation
`src/apply/trace.py`, `app/web.py::trace`, `web/pages/trace.js` (`openTrace`, drawer).

## Acceptance and tests
`tests/test_apply.py::test_the_trace_goes_from_a_number_back_to_the_news`.

## Limitations
The pre-BRD pages' numbers (dashboard, alerts, scenarios) have their own inline formulas but no trace drawer
(NFR-11 scope, Q-14).

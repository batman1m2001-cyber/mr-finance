# FEAT-09 — “Cách tính”: from a number back to the news

| | |
|---|---|
| Type | BRD capability |
| Requirements | BRD-BR-12, BRD-FR-406, BRD-NFR-11, BRD-RULE-SEC-09 |
| Users | CIO, RM, Compliance (the trace); every role (“Cách tính” on every figure, G1) |
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
and the asset-class breakdown instead (Q-14), and since F10 a client **“Cách tính”** of its own (F-D9,
`GET /api/families/{id}/how?run=`): for an effective run only, the number and its band, the formula, each
scenario's probability with the factor moves (|move| ≥ 0.05, in the model's order, with units) and the family's
change in it, the asset classes (value and contribution, loans and cards included), the event type and the
outlets — no holding, no headline, no view text.

## Every other number (G1, BRD-NFR-11)
Since G1 every money or percent figure on every page, for every role, is a control (`role=button`, keyboard
Enter/Space) that opens the drawer **“Cách tính”**: what the number is, the formula in words, its inputs with
their values, and — for staff — the function that computes it. The formulas live in one server catalogue
(`src/explain/metrics.py`, about 95 metrics, `GET /api/how`), each naming its code (`path::function`); a page renders
a figure with `n(text, metric, inputs)` and passes the inputs from the same answer as the number. A setting or a
parameter (a threshold, a return assumption, a scenario probability) says it is one and where it is set; demo
sample figures (the advisory track record) say they are sample data. Three things are not figures to explain: a
client's own words and headlines (`data-quote`), chart axis ticks (`data-axis`) and the text of an explanation
(`data-explains`).

Screens: [Tài sản](../assets/current_ui/FEAT-09-how-holdings_desktop-light.jpg) ([phone](../assets/current_ui/FEAT-09-how-holdings_phone-light.jpg)), [Kế hoạch](../assets/current_ui/FEAT-09-how-plan_desktop-light.jpg) ([phone](../assets/current_ui/FEAT-09-how-plan_phone-light.jpg)), [Phơi nhiễm, staff with the code](../assets/current_ui/FEAT-09-how-exposure_desktop-light.jpg) ([phone](../assets/current_ui/FEAT-09-how-exposure_phone-light.jpg)).

## Implementation
`src/apply/trace.py` (`trace`, `client_how`), `app/web.py::trace`, `app/web.py::family_how`,
`web/pages/trace.js` (`openTrace`, drawer), `web/pages/impact.js` (`openHow`, the client's drawer);
`src/explain/` (`catalogue.py`, `metrics.py`), `app/web.py::how_catalogue`, `web/core/core.js` (`n`, `nAttrs`,
`explainOn`, the drawer), the charts in `web/charts/` (`howOn`, `opts.metric`).

## Acceptance and tests
`tests/test_apply.py::test_the_trace_goes_from_a_number_back_to_the_news`,
`tests/test_apply.py::test_fd9_the_client_reads_how_its_number_is_made_by_asset_class_with_no_holding_named`,
`tests/ui/test_how.py::test_every_figure_on_every_route_has_its_formula` (every route of every role, the states a
click reveals and the detail pages; fails on any figure outside a metric and on any metric not in the catalogue),
`tests/ui/test_how.py::test_a_figure_opens_its_formula_by_click_and_by_keyboard`,
`tests/test_explain.py::test_every_metric_names_code_that_exists`,
`tests/test_explain.py::test_every_metric_a_page_uses_is_in_the_catalogue_and_every_one_is_used`.

## Limitations
A formula is a sentence written from its code, not generated from it: the tests prove the code exists and every
figure has a formula, not that the sentence still matches the code after a change — a reviewer does.
Figures in a chart's hover tooltip repeat a figure the page explains.

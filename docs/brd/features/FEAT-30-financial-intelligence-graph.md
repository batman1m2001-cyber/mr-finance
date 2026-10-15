# FEAT-30 — Financial Intelligence Graph

| | |
|---|---|
| Type | Extension (redesign kit), built 2026-10-16 (plan phase K3) |
| Requirements | KIT-UX-04, KIT-UX-06; respects BRD-RULE-CONTENT-01 (flow 2) |
| Users | Client (asset-class level), RM |
| Entry points | [SCR-CL-09](../ux/screens/client.md#scr-cl-09--đồ-thị-tác-động-intelligence-graph) — client Tin tác động → Đồ thị tác động, RM Khách hàng → Đồ thị tác động; `GET /api/families/{id}/graph?role=&run_id=` |
| Plan | [docs/REDESIGN_KIT_PLAN.md](../../REDESIGN_KIT_PLAN.md) phase **K3**, decision D5 |
| Status | see [traceability](../requirements/requirements_traceability.md) §4 |

## Behaviour
- `src/apply/impact_graph.py::family_graph` reads only stored records of the **EFFECTIVE** runs: news → event
  (`events.news_ids`) → scenario branch (the approved view) → factor (the branch's core shocks, plus the five
  factors that move the family most) → asset → family (the run's 3-month contribution) → goal (FR-404 goal
  impact, before → after level). Each edge lists its sources (`event`, `view`, `run` ids); valued edges carry VND.
- Wording: “có thể ảnh hưởng” / “độ nhạy” / “cú sốc ▲ vừa” — never a cause.
- Client role: news as outlet and time, events as type, assets as classes (no headline, no holding, no link).
  Staff: headlines with links, the top 8 holdings by contribution.
- Page (`web/pages/graph.js`): seven columns in SVG, edges coloured by sign and sized by value; type filters; a
  node (click, Enter or Space) lights its upstream and downstream path and opens a panel with its numbers and
  every edge with its sources; “Danh sách” shows the same edges as a table (the static alternative; the default on
  phones, where it is a stacked list).

## Implementation
`src/apply/impact_graph.py`; route in `app/web.py`; `web/pages/graph.js`; `.igraph`, `.gedge` in `web/core/tokens.css`.

## Acceptance and tests
`tests/test_graph.py`: every edge resolves to a stored record and steps one column right; asset → family values
equal the run's `by_holding`; the client sees no headline, holding or link; no run = empty graph; endpoint and 403.
UI: desktop light/dark, phone, selection — no console error, no horizontal scroll (2026-10-16).

## Limitations
- The CIO's whole-run view (all families of one run) is not built; `run_id` only narrows one family's graph.
- The goal-branch regulation notes (FEAT-10) are not drawn yet; goals come from FR-404 only.
- With three events the scenario column holds nine nodes; there is no grouping beyond the type filters.

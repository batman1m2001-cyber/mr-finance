# FEAT-30 — Financial Intelligence Graph

| | |
|---|---|
| Type | Extension (redesign kit), built 2026-10-16 (plan phase K3); overview, News Impact panel, timeline and the CIO run graph added in UI redesign R4 (2026-10-16) |
| Requirements | KIT-UX-04, KIT-UX-06, OWN-UI-04; respects BRD-RULE-CONTENT-01 (flow 2) and ADR-0008 |
| Users | Client (asset-class level), RM, CIO (whole run) |
| Entry points | [SCR-CL-09](../ux/screens/client.md#scr-cl-09--đồ-thị-tác-động-intelligence-graph) — client Tin tác động → Đồ thị tác động, RM Khách hàng → Đồ thị tác động; `GET /api/families/{id}/graph?role=&run_id=`; [SCR-CL-11](../ux/screens/client.md#scr-cl-11--bản-đồ-tài-chính-overview-graph) Bản đồ tài chính, `POST /api/overview`; [SCR-CIO-10](../ux/screens/cio.md#scr-cio-10--đồ-thị-lần-áp-dụng-run-graph), `GET /api/runs/{id}/graph`; the timeline on [SCR-CL-05](../ux/screens/client.md#scr-cl-05--tác-động-thị-trường-family-impact-client) |
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

### Overview graph (R4, R-D6)
- `src/overview` (`overview_flow`, `POST /api/overview {client_id, scope, role, goals}`) joins what other pages
  already show: the client in the centre; the asset classes held (value, count; liabilities point back to the
  client), each opening onto its holdings; the data sources; the goals the browser follows (`goals`, from Kế
  hoạch's kept list; none = the persona's defaults); the risks the dashboard flags (stress drawdown when not “ok”,
  each flagged concentration, a low reserve); the six policy items (FEAT-25) moving it most; the EFFECTIVE news
  events, joined to asset classes by the run's `by_class`.
- Every edge names its records (`holding`, `risk`, `goal`, `alert`, `run`). Holdings join a risk or a policy item
  by the names those records list; a record naming no holding links to the client. Holding-level edges carry
  `parent`, class-level ones `agg`: the UI draws the holding edge when that class is open, the class edge otherwise.
- Page `web/pages/map.js`: a radial SVG — classes on the left, sources top-left, events top-right, risks inside
  right, policy items outside right, goals along the bottom (two staggered rings) — with labels set outward.
  Sources and policy items start hidden (progressive disclosure; the side list names the policy items). A node
  (click, Enter, Space) lights its links and drops the labels of the rest; the side panel gives its figures, its
  links with their records, “Mở rộng n khoản” for a class (also double-click, `+`/`−`) and “Mở trang” to its page;
  an event opens its path on Đồ thị tác động, selected. “Danh sách” groups the same nodes by kind (the phone default).
  News edges are dashed: a potential effect, not a cause.

### News Impact panel (R4)
Selecting an event on Đồ thị tác động (client, RM) shows its direction (Tiêu cực / Tích cực by the 3-month
expected change), the main scenario, the chain it travels (each column with its count), the asset classes or
holdings it may move with this event's own share (`by_run` on the asset → family edge) and its share of net worth,
the goals' level before → after, and the news outlets.

### Timeline (R4)
`reads.family_impact` gives each item a `timeline`: the first news, the event, the view's AI draft, challenge and
CIO approval, the run's application and its current status — each with the time stored on that record. Tin tác
động shows one row per event, steps in order with their times (Vietnam time).

### CIO run graph (R4)
`impact_graph.run_graph` (`GET /api/runs/{id}/graph`): news → event → scenario → factor → asset class → every family
the run computed; class → family edges are that family's 3-month change by class. The CIO's “Đồ thị lần áp dụng”
renders it with the same page (pick a run; “Xem đồ thị” from Lần áp dụng).

## Implementation
`src/apply/impact_graph.py` (`family_graph`, `run_graph`); `src/overview/`; `src/apply/reads.py::_timeline`; routes in `app/web.py`, `app/main.py`; `web/pages/graph.js`, `web/pages/map.js`, `web/pages/impact.js`; `.igraph`, `.gedge`, `.map*`, `.m*`, `.t*` in `web/core/tokens.css`.

## Acceptance and tests
`tests/test_graph.py`: every edge resolves to a stored record and steps one column right; asset → family values
equal the run's `by_holding`; the client sees no headline, holding or link; no run = empty graph; endpoint and 403.
`tests/test_graph.py` also: an event's `by_run` shares add up to its expected change; the run graph reaches
every family and its class → family values are the stored results; the timeline's steps are the records' times.
`tests/test_overview.py`: every edge resolves to the record it names; the classes add up to assets and debts; the
client reads event types, staff headlines; the followed goals are the ones sent. Browser:
`tests/ui/test_pages.py` (overview select / expand / open path, the phone list, timeline rows, the News Impact card,
the CIO graph). UI: desktop light/dark, phone — no console error, no horizontal scroll.

## Limitations
- The overview's layout is a fixed set of sectors; with every kind on (≈ 35 nodes) a few labels still touch.
- Holdings join risks and policy items by name: two holdings of the same name in a family view are both linked.
- The goal-branch regulation notes (FEAT-10) are not drawn yet; goals come from FR-404 only.
- With three events the scenario column holds nine nodes; there is no grouping beyond the type filters.

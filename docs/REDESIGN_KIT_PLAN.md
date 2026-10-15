# OneWealth — redesign kit: findings and plan

Source: `OneWealth_Redesign_Kit.zip` (kept out of git, like the BRD): `PROMPT_MASTER.md`, `CHANGE_PROPOSAL.md`,
`BRD_COVERAGE_AND_ACCEPTANCE.md`, `PROMPT_FINANCIAL_INTELLIGENCE_GRAPH.md`, `PROMPT_ONEWEALTH_COPILOT.md`, a screenshot
of the current overview and a concept board. The kit says the board is visual direction only, not data. This plan
follows `NEWS_IMPACT_PLAN.md` (N0–N4, U1–U2 done) and does not replace it.

## 1. What the kit asks for

- Five views: **Financial Pulse** (net worth, changes, liquidity, signals), **Money Flow** (Sankey of real
  aggregated flows), **Wealth Map** (allocation with drill-down), **Financial Intelligence Graph** (news → entities →
  exposure → risk/goals), **Intelligence Feed** (what matters, why, with evidence).
- **OneWealth Copilot**: a side panel that asks, investigates, analyses, acts through real tools, navigates and
  keeps context; no hardcoded answers, no claimed success that did not happen.
- **100 % traceability**: every BRD requirement with a stable id, source, code path, UI entry, test, evidence and
  status; capabilities outside the BRD inventoried and kept.
- Motion only where it shows direction, size or a selected path; reduced-motion respected; a static alternative.

## 2. Facts checked against the repo and the BRD (2026-10-15)

| # | Fact | Evidence |
|---|---|---|
| F1 | The BRD has **61** numbered requirements: 15 BR, 34 FR, 12 NFR | ids extracted from the `.docx` text |
| F2 | The BRD never mentions a chat assistant, a Sankey or money flows between categories; "đồ thị" only means the CIO agent's 8-node graph | text search: copilot 0, hỏi đáp 0, chat 0, sankey 0 |
| F3 | The BRD forbids sending client data to an AI provider, three times: BR-11 ("AI soạn nhận định không đọc dữ liệu khách, mục tiêu, ghi chú RM"), §7.1 (the AI zone never receives client data), the data rules ("không gửi dữ liệu khách cho nhà cung cấp AI"). Explaining computed numbers must use "mẫu tất định hoặc mô hình nội bộ" | BRD text |
| F4 | Every client has 12 months of transactions with direction and category (C01: 112; categories salary, rent, pension / living, card, loan, school, health, rent_out). `src/dashboard/ops.py::cashflow` already builds history and a forecast from them | fixtures, code |
| F5 | There are **no investment purchases** in the transactions, so an "Đầu tư" flow cannot be drawn | fixtures |
| F6 | C01, Sep 2026 (personal): salary 120.4 tr in → living 17.6, card 34.8, home loan 38.0 out; 30.0 tr left | sum of the fixture rows |
| F7 | The chain news → event → approved view → factor → holding → family → goal is already stored (events, views, application runs with `by_factor` / `by_holding`, goal matches); it is not drawn as a graph | `src/events`, `src/views`, `src/apply`, `src/procedural` |
| F8 | 20 served POST graphs (dashboard, statement, declare, risk, alerts, scenario, goals, review, news, events, views, runs, research, goals/outflow) each check the caller's role on the server: they are the Copilot's natural tools | `app/main.py` |
| F9 | `NEWS_IMPACT_PLAN.md` §3 maps requirements in groups (e.g. one row for FR-101…105), without test or evidence columns, and does not list the capabilities that predate the BRD work | the plan |
| F10 | Not built: FR-306 (policy agent), FR-703 (agent catalogue), FR-801 (CIO newsletter), BR-15 (accuracy tracking) | §9 of the news plan |

Numbers on the concept board that are **not** ours and must not be copied: "90 yêu cầu / 84 đã triển khai" (F1),
"Thu nhập 180,2 tr" (C01 earns 120.4 tr), "Mua nhà 10 tỷ, 68 %" (C01's goals are Úc study fees 1.8 tỷ and a tax
payment), the "Đầu tư 50 tr" flow (F5), and tickers on the client's news card ("VHM −2,8 %": the client view shows
no tickers, BRD flow 2).

## 3. Decisions

| # | Question | Decision | Why |
|---|---|---|---|
| D1 | How the Copilot uses data | The model **routes, it never reads**: it sees the scrubbed question, the page's route and entity ids, and the tool catalogue; it returns a tool call. Our code runs the tool and writes the answer from deterministic templates over the tool's result. Default router is a keyword router (mock, labelled); the live router is `llm:copilot` | F3. It keeps BR-11 and still gives a real assistant |
| D2 | What the router may see | The question after a scrubber removes digits, amounts, account and ticker codes, and every known client, spouse and dependent name; a test asserts no fixture name or number reaches the prompt | F3; the user's own question is client data too |
| D3 | Copilot actions | Only through the existing served graphs, with the active role's user id, so the server's role and separation-of-duty checks apply unchanged. Any writing action needs an explicit confirm step in the panel; the answer reports the endpoint's real result or error | F8; the kit's "never claim success" |
| D4 | Money Flow | Built from transaction rows only: inflow categories → outflow categories + "Còn lại" (or "Thiếu hụt" when negative), per month, personal or family scope. No inferred flows, no investment band (F5) | F4, F5 |
| D5 | Graph | A view over stored records, no graph database. Every edge carries the record id it came from. Edge wording "có thể ảnh hưởng" (potential impact), never causal. Client role: event type label instead of headline, asset class instead of ticker | F7, BRD flow 2 |
| D6 | Scope vs the BRD | Pulse, Money Flow, Wealth Map, Graph, Feed and Copilot are **additions outside the BRD** (F2); the matrix lists them as such, and none may remove or hide a BRD capability or an existing page | kit rule: no silent drops |
| D7 | Look | Keep the U1 tokens (light + indigo dark). Take from the board: a compact KPI strip at the top, one visual anchor per page, the floating Copilot button. Not taken: decorative gradients, a chart on every card | kit design principles |
| D8 | Libraries | None new. Sankey and graph are drawn in SVG by `web/charts/` (as the fan chart is) | no build step today; the data is small (≤ 20 nodes per family) |

## 4. Phases

Each phase ends with its tests, desktop + phone screenshots in light and dark, and the matrix updated.

| Phase | Scope | Done when |
|---|---|---|
| **K1 matrix** | `docs/BRD_TRACEABILITY.md`: 61 rows (id, BRD section, requirement, type, code path, UI entry, dependencies, test, evidence, status: verified / partial / not built / blocked / ambiguous) + a second table of the capabilities that predate the BRD (each legacy tab and each served graph) + the additions of D6. `tests/test_traceability.py` checks the committed id list has 61 ids, each with a row and a status, and every cited test exists | 61/61 rows; every "verified" cites a test that passes; FR-306, FR-703, FR-801, BR-15 marked not built with the reason |
| **K2 Pulse, Wealth Map, Money Flow** | `GET /api/flows?client&scope&month` from transactions (D4); Sankey in `charts.js` with click-to-rows; new client/RM overview: KPI strip (net worth and change, monthly in/out/left, liquidity months, risk signal) + allocation + flow. Every number and block of the old overview is still reachable (moved, not removed) | flow bands sum to the transaction totals to the dong (test); old overview content checklist ticked item by item; reduced-motion shows a static chart |
| **K3 Graph** | `GET /api/graph?family_id` (and `?run_id` for the CIO): nodes news, event, view branch, factor, asset class/holding, family, goal; edges with source record ids (D5). SVG layout in columns (news → … → goals), not a force hairball; filter by node type; click a node to highlight its path and open the detail panel; keyboard navigation; a list view as the static alternative | every edge resolves to a stored record (test); client role sees no ticker or headline (test); no console error, no horizontal scroll |
| **K4 Intelligence Feed** | On the client and RM overviews: effective runs over the threshold, goal matches, the existing risk threshold breach, notable month-on-month changes. Each item says why it is shown and links to its evidence page | each item type has a test with its evidence link; empty state shown |
| **K5 Copilot** | `src/copilot`: tool catalogue (typed inputs, role, read/write), scrubber (D2), routers (keyword, `llm:copilot`), templates, a served graph `POST /api/copilot`. Panel: floating button, side drawer, page context, follow-up suggestions, confirm step for writes, progress and error states; conversation kept in the page session | tests: barrier (no fixture name or number in any router prompt), a client cannot run a CIO tool, no write without confirm, a failing tool is reported as failed, a live run with the configured model recorded once |
| **K6 regression and report** | Full suite, all routes × desktop/phone × light/dark, click-through flows of the news plan re-run, matrix final status, `NEWS_IMPACT_PLAN.md` §9 and this §5 updated | traceability completeness and implementation completion reported separately; every check listed with its result |

## 5. Status

| Phase | State | Commit | Evidence |
|---|---|---|---|
| K1 | matrix done; pre-BRD inventory done | (this change) | `docs/brd/requirements/requirements_traceability.md` (61 + 7 + 97 + 29 + 19 rows), checked by `tests/test_brd_docs.py` |
| K2 | done | (this change) | `POST /api/flows` is a served graph (not the GET first planned: the Copilot's tools are the served graphs, D3); old overview kept whole as “Chi tiết”; `tests/test_flows.py`; screenshots in docs/brd |
| K3 | done | (this change) | `GET /api/families/{id}/graph` (per family; the CIO's whole-run view deferred); `tests/test_graph.py`; FEAT-30 |
| K4 | done | (this change) | `POST /api/feed` (served graph); a panel of Toàn cảnh; thresholds ours (FEAT-31); `tests/test_feed.py` |
| K5 | not started | — | — |
| K6 | not started | — | — |

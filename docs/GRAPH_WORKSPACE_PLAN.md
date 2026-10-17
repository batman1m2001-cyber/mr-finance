# Graph workspace plan — the Customer's persistent financial graph (experiment)

Owner request 2026-10-17: [`docs/brd/sources/owner_requests/2026-10-17_persistent_financial_graph.md`](brd/sources/owner_requests/2026-10-17_persistent_financial_graph.md).
Requirements: **OWN-GW-01…14** ([owner_requirements.md](brd/requirements/owner_requirements.md#gw--persistent-financial-graph-2026-10-17-experiment)).
Behaviour and the capability map: [FEAT-40](brd/features/FEAT-40-persistent-financial-graph.md). Screen:
[SCR-CL-12](brd/ux/screens/client.md#scr-cl-12--không-gian-tài-chính-graph-workspace). Decision:
[ADR-0035](brd/decisions/ADR-0035-the-customer-workspace-is-one-persistent-graph.md). Streaming door:
[assistant.md §9b](brd/architecture/assistant.md).

**Status (2026-10-17): G0–G7 done** — results, gaps and performance in [graph_workspace_report.md](brd/testing/graph_workspace_report.md).

**An experiment (OWN-GW-14):** branch `exp/graph-workspace`, worktree `~/mr-finance-graph`, its own server and
public link. `main`, `~/mr-finance` and https://oneweath.ngrok.app are not touched.

## 1. Audit (2026-10-17)

| Area | What exists | What it means here |
|---|---|---|
| Shell (`web/shell.js`) | horizontal nav + subnav per role; every route replaces `#page` with a page module (ADR-0019); a draw sequence guards late renders | the Customer shell needs a long-lived workspace; the RM/staff shell stays |
| Overview graph (`web/pages/map.js`, `src/overview`) | radial SVG around the client: classes (→ holdings), sources, goals, risks, policy, events; every edge names its records; select → side panel; list view; FEAT-30 tests | the graph's base: kinds, layout, panel content and `POST /api/overview` are reused |
| Missing kinds | no income/expense nodes, liquidity only when low, no scenarios, no certainty field | added in G3 (OWN-GW-01, 12) |
| Overview cards (`web/pages/pulse.js`) | Pulse cards from `/api/dashboard` + `/api/flows`, Sankey, wealth map, feed | the strip reuses the cards (G2) |
| Assistant front end (`web/copilot.js`) | floating panel; one `POST /api/assistant` JSON reply; busy/ok/error/pending states; focus keys mark page elements (FEAT-33) | a docked mode and a streaming client (G4, G5) |
| Assistant back end (`src/assistant/turn.py`, `assistant_flow`) | `Runner.run` / `Runner.resume` of operonx-agents; template and fallback modes; audit `assistant.turn`; service untraced | `Runner.stream` exists (events `ToolCallStarted/Finished`, `TextDelta`, `ApprovalRequired`, `RunFinished`) |
| Streaming transport (operonx 1.30) | an http door whose graph has doors answers `Accept: text/event-stream` with one numbered event per `egress` item, resumable | the stream door is plain operonx (ADR-0035 §5) |
| Motion (`web/motion.js`, FEAT-33) | marks by `data-focus` keys; Web Animations tracked and paused when hidden; tests allow only transform/opacity keyframes | the graph's activity follows the same rules |
| Studio patterns (operonx-studio) | live run: active ring (transform/opacity pulse), done/failed colours, unreached faded; one particle per wire as an op fires, capped; tabbed right panel | reimplemented in the kit's tokens (no import) |

## 2. Decisions (settled)

| # | Decision | Why |
|---|---|---|
| D1 | Customer role only; RM and staff unchanged | OWN-GW-01 names the Customer; the RM's client pages are the same modules |
| D2 | The workspace (`web/workspace/`) is mounted once by the shell for the client; a route = lens + optional sheet; view state per client and scope | OWN-GW-05: no reset on navigation |
| D3 | Dedicated views are **sheets**: the existing page modules render unchanged into a panel over the mounted graph; old addresses resolve to lens + sheet | OWN-GW-11: nothing simplified; links, search and citations keep working |
| D4 | `map.js` stays for the RM; the workspace graph is a new module built from its layout and panel code (the duplication folds back if the experiment is taken) | no risk to the RM's tested page |
| D5 | `copilot.js` gains a docked mode (same module, mounted in the dock) and a streaming call; the floating panel stays for other roles | one assistant front end (FEAT-32) |
| D6 | The graph's data stays `POST /api/overview`, extended (`flow`, `liquidity`, `scenario`, `certainty`); scenario values only on request and never in totals | OWN-GW-12; one endpoint, one test file |
| D7 | `POST /api/assistant/stream`: a served graph with doors over `Runner.stream`; the browser reads it with `fetch` + a stream reader (EventSource cannot POST); `sinks = []` | OWN-GW-06…10, ADR-0035 §5 |
| D8 | Activity is keyed to events only: `step running` → the tool's nodes pulse + one particle from the centre; `step ok` → its focus keys lit; `text` → a node named in a finished step lights when the sentence arrives; `answer` → marks kept until the next question; failure → red ring and the failed step named | OWN-GW-10: nothing fabricated |
| D9 | Pan/zoom by a transform on one SVG group (pointer drag, wheel, buttons, keys); no library | OWN-GW-13: no new dependency |
| D10 | Phone: toolbar at the bottom, list view default, dock and sheets full-screen, strip folded | responsive |
| D11 | The experiment runs on port 8040 with its own copy of the state file and the same `.env` (copied, never printed), behind a Cloudflare quick tunnel (its URL is reported; it changes if the tunnel restarts) | OWN-GW-14; ngrok's one reserved domain stays on the live demo |
| D12 | Paid model calls only for a final live check (a handful of turns, cost reported); every test uses scripted models | the credit rule |

## 3. Phases

Each phase: tests, desktop + phone screenshots for UI, commit on `exp/graph-workspace` (pull first), restart the
experiment server. No PR to `main`.

| Phase | What | Requirements | Done when |
|---|---|---|---|
| G0 | Branch, worktree, port 8040, state copy, tunnel; BRD updated (OWN-GW, FEAT-40, SCR-CL-12, ADR-0035, assistant.md §9b); this plan | OWN-GW-14, 11 | the public link serves the branch; BRD checker passes |
| G1 | Workspace shell for the client: toolbar of lenses, the graph in the centre (from map.js), lens view state, sheets for every Customer page, route aliases, the dock with Trợ lý (docked copilot) and Thông tin (inspector) | OWN-GW-01, 02, 03, 05, 11 | lens switches keep the graph element, selection, opened classes; every old route resolves; the existing UI tests adapted and green |
| G2 | The bottom strip from the Pulse cards, collapsible, a card focuses its lens | OWN-GW-04 | strip renders the same figures as Toàn cảnh (test), folds and remembers |
| G3 | Data and graph: `flow`, `liquidity`, `scenario`, `certainty` in `/api/overview`; edge styles + legend; pan/zoom/fit; scenario run from the inspector as hypothetical edges | OWN-GW-01, 12 | overview tests: certainty on every node and edge, scenario in no total, flows equal the month's transactions; browser test for pan/zoom/fit |
| G4 | The stream door: `assistant_stream` service, generator op over `Runner.stream` and resume, template/fallback modes as step events then the answer, tool → nodes map in the registry; audit and conversation as the JSON door | OWN-GW-06, 07 | scripted-model tests: event order, answer identical to the JSON door's, barrier (no text events in template mode), service untraced |
| G5 | The graph follows the stream: docked panel reads events; node states (running/ok/failed), particles, progressive marks, final marks, failure feedback | OWN-GW-06…10 | browser test with a scripted stream: each state appears only after its event; no animation without an event; failure shown |
| G6 | Phone layout, keyboard, screen-reader labels, reduced motion, hidden-tab pause; performance (graph render ms, frame time during a stream, animations at once, payload) | OWN-GW-10, 13 | 390 px no horizontal scroll; reduced-motion test; numbers recorded |
| G7 | Verification and report: full suite, BRD checker, matrix statuses, screenshots, `docs/brd/testing/graph_workspace_report.md` (results, gaps, performance); one live check on the real model (cost reported) | OWN-GW-13 | report written; the owner gets the link |

### Refinement (OWN-GW-15…19, owner 2026-10-17)

Request: [`2026-10-17_graph_dataflow_refinement.md`](brd/sources/owner_requests/2026-10-17_graph_dataflow_refinement.md).
Behaviour: FEAT-40 “Hierarchy and dataflow”. The refinement keeps the page layout and every existing test, and
changes only the graph and its CSS (plus one legend line).

| Phase | What | Requirements | Done when |
|---|---|---|---|
| G8 | Hierarchy: the three layers, holdings on select (no openAll), relations on demand, the label collision pass, quieter background | OWN-GW-15 | visible edges and crossings counted before and after per lens; no two labels overlap (browser check, desktop + phone); existing tests green |
| G9 | Dataflow: silk edges by certainty, money knobs, comet pulses (head + trail, transform only, flicker), arrival reaction, stream events mapped to lit paths, two hops, dimming, writing state, failure in red | OWN-GW-16, 17, 18 | browser tests with a stubbed stream: lit paths only after `step`, comets toward the centre only after an ok end, none after a failure, hollow on hypothetical, dimming cleared on reset; motion-rule test still passes |
| G10 | Performance and report: a 3× synthetic graph, frame times during a stream burst, the comet cap, reduced motion; screenshots; report and matrix | OWN-GW-19, 13 | numbers in graph_workspace_report.md; matrix rows verified; demo link updated |

## 4. Risks

- **UI tests that drive Customer routes** find their content in a sheet now: adapted in G1, never deleted.
- **The RM's client pages** use the same modules: a module must not assume it owns the page (sheets give it a box,
  as `#page` did).
- **Stream disconnects:** operonx keeps the events 15 minutes and resumes by `after_seq`; the panel falls back to
  the JSON door if the stream cannot open.

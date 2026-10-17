# The graph workspace report (G7, 2026-10-17, experiment)

**Verdict: built and verified on the experiment branch.** All of OWN-GW-01…14 are built and covered by tests.
For a Customer, the app is now one page:

- a persistent graph around Tài sản ròng;
- a toolbar of lenses on the left;
- a dock on the right holding the assistant and the inspector;
- a strip of summary cards at the bottom that folds away.

Every old Customer page still opens, as a sheet over the graph. The graph moves only when the assistant's real
stream says something happened, and it says so when a stream breaks. Some gaps are left; they are listed below.

The experiment runs on branch `exp/graph-workspace` with its own server (:8040) and public link. `main` and the
live demo on :8030 are unchanged.

Plan: [GRAPH_WORKSPACE_PLAN.md](../../GRAPH_WORKSPACE_PLAN.md). Behaviour:
[FEAT-40](../features/FEAT-40-persistent-financial-graph.md). Screen: SCR-CL-12. Decision: ADR-0035.

## Results by requirement

| Req | What was checked | How |
|---|---|---|
| OWN-GW-01 | One SVG around Tài sản ròng, with the in and out cash flow, the reserve and the stress scenarios as nodes | `tests/test_overview.py::test_the_workspace_kinds_money_reserve_and_scenarios`; browser |
| OWN-GW-02 | A toolbar of 6 lenses plus Chuyên gia and Bộ nhớ, with tooltips; arrow keys and Enter change the lens | `tests/test_graph_workspace.py`, `tests/ui/test_graph_workspace_ui.py::test_keyboard_and_phone` |
| OWN-GW-03 | The dock: Trợ lý is docked, with no floating button; Thông tin opens when a node is selected | `tests/ui/test_graph_workspace_ui.py::test_the_inspector_the_strip_and_a_hypothetical_scenario` |
| OWN-GW-04 | The strip shows the five Toàn cảnh cards from the same reads; a card focuses its lens; folding is remembered | the same test |
| OWN-GW-05 | The same SVG element stays across six lenses and a sheet; an old address (`#/client/tai-san`) opens its page as a sheet; Escape closes it | `::test_one_page_the_graph_survives_lenses_and_sheets` |
| OWN-GW-06 | `POST /api/assistant/stream` sends one step for each real tool start and end, with the nodes it reads; the fallback path does the same | `tests/test_assistant_stream.py` (7 tests); `::test_the_assistant_stream_drives_the_graph` (real server, keyword path) |
| OWN-GW-07 | Text events come only in model mode; a stress test puts its effect on its scenario node | `tests/test_assistant_stream.py::test_template_mode_streams_no_text_from_the_model`, `::test_a_stress_test_puts_its_effect_on_its_scenario_node` |
| OWN-GW-08 | The answer's focus keys stay marked on the graph | `::test_the_assistant_stream_drives_the_graph` |
| OWN-GW-09 | A broken stream is reported ("Mất kết nối với trợ lý giữa chừng…") and its running nodes are marked failed; a failed tool lights nothing | `::test_a_broken_stream_is_said_and_marked_failed`, `tests/test_assistant_stream.py::test_a_failed_tool_is_said_failed_and_lights_nothing` |
| OWN-GW-10 | Nothing loops (no `setInterval`); transitions use only transform and opacity; every Web Animation is tracked; no particles under reduced motion | `tests/test_graph_workspace.py::test_the_workspace_is_served_and_follows_the_motion_rules`; the reduced-motion browser test |
| OWN-GW-11 | Every page of the old Customer menu has an entry point; every server-built Customer link resolves | `::test_every_customer_page_has_an_entry_point`, `::test_every_route_the_server_builds_for_a_customer_resolves` |
| OWN-GW-12 | Every edge carries a certainty: actual, estimate (dashed) or hypothetical (dotted). A scenario run shows "nếu xảy ra −1,82 tỷ" on its node, the inspector says "không cộng vào tài sản ròng", and net worth stays 43,5 tỷ | overview test; `::test_the_inspector_the_strip_and_a_hypothetical_scenario` |
| OWN-GW-13 | This report and the tests | 18 new tests (6 + 7 + 5) |
| OWN-GW-14 | Branch, worktree, port 8040 and a tunnel; with `MF_JOBS=off` the second copy runs no job | `::test_a_second_copy_of_the_app_runs_no_job_on_its_own` |

**Full suite:** 714 passed, 1 skipped (15 min, `tests/` without e2e). **BRD checker:** 0 errors. Owner requests: 49 verified, 3 unverified, 1 not applicable.

## The real model, once

One question went through the stream on :8040: "Tài sản của tôi thế nào và tháng này tôi chi bao nhiêu?" (client
C01, model mode).

- **Events:** `start`, then `tong_quan` and `dong_tien` started together (parallel tool calls) and ended, then 50
  text deltas, then `answer`.
- **Answer:** status ok. The numbers match the graph: 43,53 tỷ, cash in 120,4 triệu, cash out 90,4 triệu.
- **Time and cost:** 5.4 s wall clock, 2 model requests, 10,670 input and 578 output tokens, **US$0.0014**.
- **Request count:** this was the only paid call of the phase. All the tests use a scripted model or the keyword
  path.

## Performance

Measured with headless Chromium using software rendering (no GPU), so a real browser will be faster:

| Measure | Value |
|---|---|
| First graph drawn (sign-in to nodes on screen) | 1.3–1.4 s |
| `POST /api/overview` / `/api/dashboard` / `/api/flows` | 188–254 ms / ~190 ms / ~190 ms |
| Lens switch: mean frame / worst frame | 17–19 ms / 33–67 ms |
| JS busy time over four lens switches | 551 ms before G6, 125 ms after; layout reads are batched, the size comes from a ResizeObserver, and returning nodes fade in after two frames |
| Select a node → inspector shown | ~190 ms |
| Open a sheet | ~343 ms |
| SVG elements | 555 |
| Particles during a stream | at most 6; none under reduced motion |

## Screenshots

Desktop and phone, dark theme, demo client C01:

- [Desktop, Tổng quan lens](../assets/current_ui/SCR-CL-12_desktop-dark.jpg)
- [Desktop, an old address as a sheet](../assets/current_ui/SCR-CL-12-sheet_desktop-dark.jpg)
- [Phone, Tổng quan lens](../assets/current_ui/SCR-CL-12_phone-dark.jpg)
- [Phone, the dock](../assets/current_ui/SCR-CL-12-dock_phone-dark.jpg)
- [Phone, an old address as a sheet](../assets/current_ui/SCR-CL-12-sheet_phone-dark.jpg)
- [A stream in flight: lit paths and pulses](../assets/current_ui/SCR-CL-12-dataflow_desktop-dark.jpg)
- [A failed read in red, a scenario's hollow pulse](../assets/current_ui/SCR-CL-12-failed_desktop-dark.jpg)

## Refinement: hierarchy and dataflow (G8–G10, OWN-GW-15…19)

The owner asked for a cleaner graph with Studio-style data flow
([request](../sources/owner_requests/2026-10-17_graph_dataflow_refinement.md)). The patterns were studied from
OperonX Studio's data-flow view and adapted to FEAT-33's motion rule (transform and opacity only); see FEAT-40
“Hierarchy and dataflow”.

**Clutter, before and after** (measured in the browser on every lens; desktop 1440×900 / phone 390×844):

| Lens | Edges | Crossings | Labels overlapping | Nodes overlapping |
|---|---|---|---|---|
| Tổng quan | 31 → 20 | 104 → 0 | 3 → 0 (phone 17 → 0) | → 0 |
| Tài sản | 51 → 9 (holdings on pick) | 163 → 0 | 4 → 0 (phone 5 → 0) | → 0 |
| Tin & sự kiện | 27 → 17 | 127 → 0 | 5 → 0 (phone 18 → 0) | 6 → 0 |
| Rủi ro | 13 → 12 | 8 → 0 | 1 → 0 (phone 7 → 0) | → 0 |
| Dòng tiền, Mục tiêu | 12, 9 (unchanged) | 0 | 3 → 0, 0 | → 0 |

How the clutter was removed:
- Only the spokes of “My Wealth” are drawn by default. A news, policy or risk item has one derived spoke carrying
  its own total, “tổng hợp từ n liên kết”, instead of its fan of class edges.
- Relations show only for the node that is picked or pointed at, or for the exact path a pulse takes.
- Holdings open when their class is picked.
- Crowded arcs use two rings, and a short relaxation pass separates nodes.
- Each label takes its first free place. With no free place, its figure line is dropped; then the label shows only
  on demand.
- The centre's text now fits in its disc: four short lines on a 62 px disc. The old 128 px line crossed the border.

**Dataflow** (OWN-GW-16…18):
- The edges are silk hairlines.
- A path being read glows in the pulse colour (teal: never the blue or orange of money). A path whose read failed
  turns red.
- When results arrive, comets run home to “My Wealth”: a bright head with a three-dot trail and a flicker, at
  520 px/s. “My Wealth” bursts as each one arrives.
- News goes through the two classes it moves most.
- A scenario's pulse is hollow.
- A failed tool sends no pulse.
- The centre shows a writing state while text streams.
- After the answer, its paths stay lit and the rest stays dimmed until a background click or the next question.
- The legend says “Xung sáng: trợ lý đọc dữ liệu, không phải giao dịch”.
- Verified by `tests/ui/test_graph_workspace_ui.py::test_the_dataflow_follows_the_stream_and_only_the_stream`:
  - at rest, nothing glows and no comet exists;
  - while tools run, their paths glow and no comet runs yet;
  - the failed read gives exactly 4 red paths and 0 comets;
  - the scenario's read sends a hollow comet;
  - the writing state shows, then the kept marks;
  - a background click clears everything.
- Under reduced motion there are 0 comets and 0 bursts at every sampled moment, with the same lit and red states.

**Performance** (OWN-GW-19; headless Chromium with software rendering, no GPU):

| | Real graph (60 nodes) | 3× graph (168 nodes) |
|---|---|---|
| Lens switch: mean / worst frame | 17–18.5 ms / 33–67 ms | 18–21 ms / 83–183 ms (one native style and layout task of 76–147 ms; JS ≈ 12 ms) |
| Burst of 8 tools ending together: mean / p95 frame | 18.2 ms / 33 ms | 22 ms / 50 ms |
| Comets at once | ≤ 8 (the cap) | ≤ 8 |
| SVG elements | 612 | 1,682 |

Two fixes came from profiling:
- **The chat bubble:** the live bubble redrew and laid out the whole message list on every stream event, taking
  1.2 s of JS in a 37-event burst. It now redraws at most every 60 ms.
- **The edges:** they were rebuilt on every event. Now they are only restyled when the visible set is unchanged.

The SVG drop-shadows were suspected and ruled out: with every filter turned off the numbers were unchanged.

**Gaps left:**
- On the 3× graph, a lens switch still costs one native style and layout task of about 100–150 ms in software
  rendering.
- On a phone, a few labels in a crowded arc show only on demand.
- Comets are skipped while the tab is hidden; they don't queue.

## Found and fixed while verifying

- **The staff map crashed on the new node kinds.** `web/pages/map.js` had no look for `flow`, `liquidity` and
  `scenario`. It now draws only the kinds it has a look for, so staff see the map as before. Caught by
  `tests/ui/test_how.py` and the RM "internal" stamp check.
- **On a phone, an open sheet covered the dock.** The sheet was a fixed full-screen layer, so the assistant could
  not be used while it was open. On a phone the sheet now takes the graph's place in the page (the graph stays
  mounted, hidden) and the dock stays below it. Covered by `::test_keyboard_and_phone`.

## Gaps

- **Sheets use viewport media queries.** Some page tables in a sheet clip at around 990 px wide, because the pages
  were laid out for the whole window.
- **No resume after a dropped stream.** The door numbers its events and can resume (`after_seq`), but the panel
  does not use this yet. A drop is reported as a failure and the person asks again.
- **The failed-tool stream test is conditional.** It asserts only when the scripted tool really fails for C05.
  Failure marking itself is proven by the browser test with a broken stream.
- **Old UI tests, adapted (16).** These tests were written for the old Customer layout: the menu, the floating
  copilot button and the map page.
  - The floating panel's marks, states and phone behaviour now run as the RM, who keeps that panel. The refusal and
    conversation checks still run as the Customer, on the docked panel.
  - The map page tests run on the RM's map. For the Customer, that page is now the graph.
  - A figure's `data-focus` is counted inside the page, because the strip repeats the cards.
- **Experiment only.** Staff roles (RM, CIO, Compliance, Admin) keep the previous layout. Nothing is merged to
  `main`.

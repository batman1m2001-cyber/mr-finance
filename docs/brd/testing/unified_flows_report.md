# The unified graph and its money flows — report (2026-10-17, experiment)

**Verdict: built and verified on the experiment branch.** OWN-GW-33…50 are built and covered by tests, with one
named gap. Transfers are not drawn because the data has no transfer rows (OWN-GW-34, partially implemented).

The Customer's graph is now one money model:
- **Actual:** what really moved, drawn as bright sparks that run the way the money goes, as much as it is.
- **Estimate:** what the CIO's assumptions estimate, drawn as even dashes.
- **Hypothetical:** what the person supposes, drawn as hollow dots, only while a scenario is active.

Several scenarios combine on the server with nothing counted twice, and none is ever added to net worth. A picked
node or edge says where it comes from, how it is computed, what it assumes and what it reaches. The assistant knows
the lens, the selection and the active scenarios. It can read a node's links and compare scenarios, and the graph
lights what it reads.

Plan: [UNIFIED_FLOWS_PLAN.md](../../UNIFIED_FLOWS_PLAN.md) (F1–F12, U0–U5, V). Behaviour: FEAT-40 “Money flows,
scenarios and the assistant”, its “As built” notes and its “Feature map”. Source: SRC-05 (the owner's request of
2026-10-17). Branch `exp/graph-workspace`, served on :8040. `main` and the live demo on :8030 are unchanged.

## What was built

| Phase | Commit | What |
|---|---|---|
| U0 | f17b418 | BRD: the request, OWN-GW-33…50, the FEAT-40 section, the plan |
| U1 | 1e25f04 | Data: amount, monthly rate and direction on every money edge; goals sharing one pool; the month's categories; stress rows by class; `POST /api/scenario/combine`; the person's own what-if |
| U2 | bc550db | Motion from the data: intensity from the monthly rate, three certainty looks, direction, at most 48 spark paths, sleep off screen |
| U3 | dd3e1b1 | Scenarios on the graph: activate, the combined bar, hypothetical class and cost edges, the what-if form, the trace in Thông tin |
| U4 | d82648a | Edge selection (mouse and keyboard) with source, formula, assumptions, confidence and downstream; categories on Dòng tiền; one shared goal pool |
| U5 | 8659cbb | The assistant sees the graph: the workspace in the request, checked on the server; `lien_ket`, `so_sanh_kich_ban`; the stream lights what each read |
| V | this commit | The audit with scenarios active: an active scenario now reaches the core on one spoke; a tight route for the phone; routes end on the rims; another member's holdings marked on the graph; the agent map knows the graph tools; the layout test runs with scenarios on and counts short edges; this report, the matrix, the feature map |

## The layout audit

`layout_audit.py` (scratch) and its test form `tests/ui/test_graph_layout_ui.py` count in screen pixels on every
lens, desktop and phone. Each lens is measured idle and then with every node picked in turn. A pick of income or
spending on Dòng tiền opens its categories, so “picked” includes the categories open. Worst lens, worst pick:

| Graph · state | discs overlap | labels overlap | label on a disc | edge through a node | edge through a label | crossings | edge short of its node |
|---|---|---|---|---|---|---|---|
| Real, no scenario, idle and picked | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3×, no scenario, idle and picked | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Real, two scenarios active, idle — **before V** | 0 | 0 | 0 | 0 | 1 | 27 | — |
| Real, two scenarios active, picked — **before V** | 0 | 0 | 0 | 0 | 1 | 18 | 1 (10 px) |
| Real and 3×, two scenarios active, idle and picked — **after** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**What the audit found and how it was fixed.**
- **An active scenario drew its whole fan of class edges all the time.** The fan cut across the ring: 27 crossings
  on desktop Tổng quan, 9 on the phone, 3 on Mục tiêu. Now an active scenario reaches the core on its own spoke,
  which carries its whole change (class shocks and costs) and moves in hollow dots. Its fan shows when it is picked
  or read by the assistant, when the rest steps back. This is the rule news items already follow.
- **Another family member's holdings were not marked on the graph.** The server marked them (`owner`,
  `family`), but only Thông tin said whose they were. In Gia đình, each such holding or category now carries the
  member's initial on its rim, named on hover; a category shared by two people shows “2”. There is still one core,
  the family's total. A centre per member is a design question left to the owner.
- **Some edges stopped short of their circle** (10 px on the phone route below). Every sampled route now begins and
  ends on the rims, and the audit and the layout test count any end more than 4 px off.
- **On a phone, a picked scenario's edge ran through another scenario's label.** The ring sits close to the core
  there, so the inner route only dipped a few pixels below the ring. A last candidate route now runs at a fixed
  radius in the gap just outside the core's rings. It is tried only when every other route is blocked, so no route
  that was clear before has changed.

## Results by requirement

| Req | What was checked | How |
|---|---|---|
| OWN-GW-33 | One graph per Customer: classes, holdings, sources, income, spending and categories, repayments, liquidity, risks, news, policy, goals, scenarios. Lenses refocus it, sheets open over it, and every BRD feature is mapped to its graph form | FEAT-40 “Feature map”; `tests/ui/test_graph_workspace_ui.py::test_one_page_the_graph_survives_lenses_and_sheets` |
| OWN-GW-34 | Actual money edges with amount, monthly rate, direction and the records they sum. **Gap:** no transfer rows exist | `tests/test_overview_flows.py`; `tests/ui/test_graph_flows_ui.py::test_sparks_run_the_way_the_money_goes_and_only_on_amounts` |
| OWN-GW-35 | News: the 3-month change per class with its P10/P90. Policy: an amount only where one class takes it | `tests/test_overview_flows.py::test_a_news_edge_moves_its_three_month_change_over_three_months_and_keeps_its_band`, `::test_a_policy_item_has_an_amount_only_where_one_class_takes_it` |
| OWN-GW-36 | Each goal's monthly saving; goals sharing a pool say so once, against the surplus | `tests/test_overview_flows.py::test_a_goal_edge_is_the_monthly_saving_it_needs_and_shared_pools_are_said_once`, `tests/ui/test_graph_edges_ui.py::test_goals_sharing_a_pool_say_it_once_against_the_surplus` |
| OWN-GW-37 | Five stress tests and the person's what-if as hypothetical edges | `tests/test_scenario_combine.py`, `tests/ui/test_graph_scenarios_ui.py::test_the_persons_what_if_takes_their_inputs_within_bounds` |
| OWN-GW-38 | Three certainties drawn and named apart; family marks; no scenario in any total | `tests/ui/test_graph_flows_ui.py::test_an_estimate_does_not_look_like_a_real_transfer`, `tests/ui/test_graph_scenarios_ui.py::test_active_scenarios_combine_on_the_server_and_never_touch_net_worth`, `tests/test_scenario_combine.py::test_the_records_are_never_touched` |
| OWN-GW-39 | The trace: assumptions → classes → costs → liquidity → projected net worth → goals | `tests/ui/test_graph_scenarios_ui.py::test_the_trace_runs_from_the_assumptions_to_the_goals` |
| OWN-GW-40 | Shocks compound per holding, the parts add up, a shared cost counts once; the bar shows the server's figure | `tests/test_scenario_combine.py` (8 tests), `tests/ui/test_graph_scenarios_ui.py::test_active_scenarios_combine_on_the_server_and_never_touch_net_worth` |
| OWN-GW-41 | Sparks per beat, speed, trail and opacity grow with the monthly amount; direction from the money; relations still | `tests/ui/test_graph_flows_ui.py` (5 tests) |
| OWN-GW-42 | A tool's start lights what it reads; an active scenario's read pulses along its own edges, hollow | `tests/ui/test_graph_assistant_ui.py::test_a_question_carries_the_workspace_and_a_comparison_lights_its_scenarios`, `tests/test_assistant_graph.py::test_the_stream_lights_what_each_read` |
| OWN-GW-43 | The core and its hierarchy are unchanged by the flows | `tests/ui/test_wealth_core_ui.py` |
| OWN-GW-44 | The layout requirements hold with scenarios active and categories open, real and 3× | the audit above; `tests/ui/test_graph_layout_ui.py::test_every_lens_is_clear_idle_and_with_a_pick` (now also with two scenarios on) |
| OWN-GW-45 | `lien_ket` and `so_sanh_kich_ban` answer from the server's own numbers | `tests/test_assistant_graph.py::test_links_are_the_overviews_own`, `::test_the_comparison_is_the_engines_own_alone_and_together`; the real-model turn below |
| OWN-GW-46 | A picked node or edge shows Nguồn, Cách tính, Giả định, Độ tin cậy (only where recorded) and Ảnh hưởng tiếp theo | `tests/ui/test_graph_edges_ui.py::test_a_picked_edge_says_where_it_comes_from_and_what_it_reaches` (news, goal, money, scenario), `::test_an_edge_is_picked_by_keyboard` |
| OWN-GW-47 | The request carries the lens, the selection and the active scenarios, checked on the server; the label reaches a model only | `tests/test_assistant_graph.py` (6 tests) |
| OWN-GW-48 | Same SVG and CSS; sleep off screen and under a sheet; still under reduced motion; frame times below | `tests/ui/test_graph_flows_ui.py::test_everything_pauses_off_screen_and_under_a_sheet`, `::test_nothing_moves_under_reduced_motion` |
| OWN-GW-49 | Nothing invented: no amount on a relation or on a policy item touching several classes, no confidence where none is recorded, no transfer without rows | `tests/test_overview_flows.py::test_money_edges_say_how_much_a_month_and_which_way_relations_say_nothing`, `tests/ui/test_graph_edges_ui.py` |
| OWN-GW-50 | No feature removed; the BRD updated; this report | the suites below; `scripts/check_brd_docs.py` |

## The assistant, on a real model

One turn on :8040 with two scenarios active and the tuition goal picked: “Nếu hai kịch bản đang bật xảy ra cùng lúc
thì tài sản và mục tiêu đang chọn ra sao?” The model called `so_sanh_kich_ban` and `lien_ket` on its own. It
answered with the combined bar's figures: 43,53 → 39,65 tỷ (−3,87 tỷ); alone −1,82 and −2,22 tỷ; 164,4 triệu less
than their sum because the shocks overlap. The first run showed that the comparison named only the goals whose
status changed, so “this goal” had no answer. The tool now names every goal's status, the picked one first, and
the second run said “Học phí cho con… chậm tiến độ, kịch bản không làm thay đổi”. Two runs, 4 model requests,
US$0.0036 in all.

## Frame times

Headless Chromium with software rendering (no GPU), Tổng quan, desktop 1440×900, median of 3 runs. The baseline is
U1 (1e25f04, the data only, before any motion change): its `graph.js`, `workspace.js`, `inspector.js`, `lenses.js`
and `tokens.css`, served against the same server, with the same scripted burst (8 tool steps, 20 text events, an
answer).

| Graph | Idle mean | Idle p95 | Burst mean | Burst p95 | Burst worst frame |
|---|---|---|---|---|---|
| Real — U1 | 16.71 ms | 16.8 ms | 17.91 ms | 33.2 ms | 83 ms |
| Real — after | 17.37 ms | 16.8 ms | 20.35 ms | 33.4 ms | 117 ms |
| 3× — U1 | 16.69 ms | 16.7 ms | 18.58 ms | 33.3 ms | 117 ms |
| 3× — after | 16.69 ms | 16.8 ms | 20.00 ms | 33.4 ms | 150 ms |

- **Idle:** within the plan's gate. The real graph's idle mean is +0.66 ms (the gate is 1 ms), and p95 is unchanged.
  More edges now carry sparks (goals, news, categories), and they cost that much.
- **Bursts:** the mean is 1.4–2.4 ms slower and p95 is unchanged. The worst single frame grew by about 33 ms, one
  dropped frame at 60 Hz, on both graphs. This is software raster with no GPU, so a real browser will do better.
  The cost is recorded here, not hidden.

## Suites

All runs below were made with `.env` moved aside, so no model is called.

| Suite | Result |
|---|---|
| Top level (`tests/`, without `tests/ui`) | 703 passed, 1 skipped, 8 failed before the V fixes. Seven were the agent map not knowing `assistant.graphtools` (a U5 regression, fixed); one was this report's missing link. The affected files were rerun after the fixes: 29 passed (`test_agent_map`, `test_access`, `test_brd_docs`, `test_graph_workspace`, `test_assistant_graph`). |
| Browser (`tests/ui`), full | 84 passed, 1 failed: `test_routes.py[desktop-light]`, the test server dropping a login under load. Rerun alone: 4 of 4 passed. |
| Browser, the graph files after the last fixes (rims, family marks) | 42 passed, 1 failed: the new family-mark test read the badge's hover title with its letter. The test was fixed and passes. |
| Assistant and Copilot (`test_assistant*.py`, `test_copilot.py`) | 256 passed (U5) |

## Gaps and trade-offs

- **Transfers (OWN-GW-34).** The demo data has no transfer rows, so no transfer is drawn and none is invented.
- **Confidence (OWN-GW-46, 49).** Only news edges have a recorded band (P10/P90). Goals, scenarios and actual
  records say “Không có độ tin cậy” instead of a made-up score.
- **A policy item touching several classes** has no amount on its edges. The data gives one total, not a split.
- **Scenarios are one-offs.** They have no monthly rate. Their motion is relative to the largest of their kind,
  capped at half the strength of a month's main flow.
- **An active scenario's fan shows on demand.** At rest, its spoke carries the whole change. The class and cost
  edges show when it is picked or read (see the audit).
- **Categories open on Dòng tiền only.** A pick on Tổng quan must move no node. Their nodes are small and sit close
  to their flow, so their names show on hover or in Thông tin, not beside them (screenshot “Dòng tiền”).
- **Small amounts are shown in đồng.** In Thông tin, a few downstream effects under 1 triệu read in đồng
  (“−221.718 đ”) among figures in triệu and tỷ. It is correct, but harder to compare.
- **The strip has no goal line.** The goals' total sits in Thông tin, because the line cost 38 px of graph on every
  lens.
- **The graph tools need a model.** Without one, the keyword path keeps the Copilot's 13 tools and the instructions
  get the selection's kind, not its name.
- **Life events are not combinable scenarios.** They are the goals (FEAT-26), as the plan's scope says.

## BRD requirements not yet implemented

After this work, 7 matrix rows of 310 are neither verified nor not applicable, and none of them is planned or
blocked:

| Row | Status | What is missing |
|---|---|---|
| OWN-GW-34 | partially_implemented | Transfers: no transfer rows in the data (above) |
| BRIEF-RISK-04 | partially_implemented | Say-vs-do is built; the re-ask triggers are not (Q-16) |
| KIT-UX-06, KIT-UX-07 | implemented_unverified | Built and checked by hand and screenshots in the K6 sweep; no automated UI test covers every route at both widths |
| OWN-MOTION-01, OWN-MOTION-05 | implemented_unverified | Measured in a browser run (panel ripple, nothing moving at rest); no suite test |
| OWN-UI-06 | implemented_unverified | The live models on the public demo, checked by screenshots; a run against live models is not a suite test |

The BRD's own 61 numbered requirements, its 7 success metrics and its 97 rules are all implemented and verified, or
not applicable (2 rules).

## Screenshots

- [Dòng tiền, categories open](../assets/current_ui/SCR-CL-12-flows_desktop-dark.jpg) ·
  [phone](../assets/current_ui/SCR-CL-12-flows_phone-dark.jpg)
- [Two scenarios active](../assets/current_ui/SCR-CL-12-scenarios_desktop-dark.jpg) ·
  [phone](../assets/current_ui/SCR-CL-12-scenarios_phone-dark.jpg)
- [A picked news edge in Thông tin](../assets/current_ui/SCR-CL-12-edge_desktop-dark.jpg) ·
  [phone](../assets/current_ui/SCR-CL-12-edge_phone-dark.jpg)
- [The assistant comparing scenarios](../assets/current_ui/SCR-CL-12-compare_desktop-dark.jpg) ·
  [phone](../assets/current_ui/SCR-CL-12-compare_phone-dark.jpg)

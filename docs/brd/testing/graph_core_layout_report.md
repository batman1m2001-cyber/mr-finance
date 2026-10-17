# The central wealth core and the graph's layout — report (2026-10-17, experiment)

**Verdict: built and verified on the experiment branch.** OWN-GW-20…32 are built and covered by tests. On every
lens, on desktop and phone, with the demo client's graph and with one three times its size, idle and with every
node picked in turn, the audit counts **zero**:
- overlapping discs or labels;
- labels on discs;
- edges through a node or a label;
- crossings between strong edges.

The core is layered, moves slowly, and its ports and band keep the money sparks' beat. It costs no measurable frame
time.

Plan: [GRAPH_CORE_LAYOUT_PLAN.md](../../GRAPH_CORE_LAYOUT_PLAN.md). Behaviour: FEAT-40, “The centre and the layout”
and its “As built” notes. Sources: SRC-05 (two owner requests, 2026-10-17). Branch `exp/graph-workspace`, served on
:8040. `main` and the live demo on :8030 are unchanged.

## The audit, before and after

`layout_audit.py` (scratch) and its test form `tests/ui/test_graph_layout_ui.py` count in screen pixels on the six
lenses. Each lens is measured idle, then with every node picked in turn. Worst lens, worst pick:

| Graph · view | discs overlap | labels overlap | label on a disc | edge through a node | edge through a label | crossings |
|---|---|---|---|---|---|---|
| Real, desktop, idle — before | 0 | 0 | 0 | 3 | 7 | 0 |
| Real, desktop, idle — **after** | 0 | 0 | 0 | 0 | 0 | 0 |
| Real, desktop, picked — before | 0 | 1 | 3 | 9 | 6 | 0 |
| Real, desktop, picked — **after** | 0 | 0 | 0 | 0 | 0 | 0 |
| Real, phone, idle — before | 0 | 1 | 0 | 6 | 5 | 0 |
| Real, phone, picked — before | 0 | 2 | 3 | 13 | 4 | 0 |
| Real, phone, idle and picked — **after** | 0 | 0 | 0 | 0 | 0 | 0 |
| 3×, desktop Tổng quan, idle — before | 0 | 0 | 0 | 38 | 17 | 0 |
| 3×, desktop Tổng quan, picked — before | 0 | 2 | 4 | 66 | 6 | 0 |
| 3×, every lens, desktop and phone, idle and picked — **after** | 0 | 0 | 0 | 0 | 0 | 0 |

The last audit run found two defects, and both are fixed:
- **An open class's label sat on its own holding** where the class sits at a corner of the ring (Bất động sản on
  desktop Tài sản). The label now takes the first side clear of its holdings and of its own spoke. The test now picks
  every class on Tài sản, not one of each kind.
- **Opening a big group on the 3× graph overlapped discs** (17 assets on a phone). Before the fix, when nothing else
  could fold, the layout squeezed. Now the group opens partly: its largest members show, and the rest stay behind
  “+n khác” (“không đủ chỗ để mở hết”, all of them in Danh sách). Squeezing is left only for a ring that cannot hold
  even what never folds (the selection, an open class, money in and out, the reserve). No tested graph reaches it.

## Results by requirement

| Req | What was checked | How |
|---|---|---|
| OWN-GW-20 | The core's layers: aura, two rings, lit bezel, glass body, inner light, highlight, a darker face under the figures; theme tokens for light and dark | screenshots SCR-CL-12-core dark and light; `tests/ui/test_wealth_core_ui.py::test_the_net_worth_stays_readable_whatever_the_light` |
| OWN-GW-21 | Ambient motion: a 7 s breath and a drifting ring; no spin, no particles; selection stops the breath | `tests/ui/test_wealth_core_ui.py::test_the_core_answers_selection_the_assistant_and_a_flow` |
| OWN-GW-22 | Ports peak as each spark arrives (income) or leaves (spending, repayments); the band crosses on the income's arrival and the out-flows leave 0.36 s later; read off the animations' own clocks, within 20 ms | `tests/ui/test_wealth_core_ui.py::test_the_ports_and_the_band_keep_the_sparks_beat` |
| OWN-GW-23 | The net worth keeps ≥ 7:1 contrast against the brightest the core gets behind it (8 frames through a beat), dark and light | `tests/ui/test_wealth_core_ui.py::test_the_net_worth_stays_readable_whatever_the_light` |
| OWN-GW-24 | States on the real events: selected (accent rim), a tool running (data colour, faster breath), streaming (a ripple per text event, none left after), a flow picked (the band takes its tone, other ports step back) | `tests/ui/test_wealth_core_ui.py::test_the_core_answers_selection_the_assistant_and_a_flow` |
| OWN-GW-25 | Same SVG and the sparks' CSS clock; opacity and transform only; nothing runs under reduced motion; idle frame cost equal to before | `tests/ui/test_wealth_core_ui.py::test_nothing_of_the_core_moves_under_reduced_motion`; frame times below |
| OWN-GW-26 | No overlap of discs or labels, labels on canvas and never hidden for room, desktop and phone | `tests/ui/test_graph_layout_ui.py::test_every_lens_is_clear_idle_and_with_a_pick` |
| OWN-GW-27 | One ring in a fixed group order around the centre; groups fold into “+n” nodes instead of squeezing | `tests/ui/test_graph_layout_ui.py::test_a_dense_graph_folds_instead_of_squeezing` |
| OWN-GW-28 | No edge through a node or a label; no crossing strong edges, idle and with every pick | `tests/ui/test_graph_layout_ui.py::test_every_lens_is_clear_idle_and_with_a_pick` |
| OWN-GW-29 | Money edges strongest, then holdings and classes, then summaries; estimates dashed, hypotheses dotted, actual solid; a pick keeps its own edges strong and drops the rest below 0.1 | `tests/ui/test_graph_layout_ui.py::test_the_edges_say_what_they_are_and_only_the_picked_ones_stand_out` |
| OWN-GW-30 | Group open and close; Tập trung fits the selection and its neighbours with the rest dimmed; `0` returns to the fit, `f` focuses again | `tests/ui/test_graph_layout_ui.py::test_a_dense_graph_folds_instead_of_squeezing`, `tests/ui/test_graph_layout_ui.py::test_focus_fits_the_selection_and_keeps_the_rest_in_sight` |
| OWN-GW-31 | A pick outside Tài sản moves no node; an answer moves no node; lens switches keep the order round the ring | `tests/ui/test_graph_layout_ui.py::test_the_layout_holds_still` |
| OWN-GW-32 | The audit on the real and the 3× graph, desktop and phone; frame times; this report | the two test files (12 tests); the tables here |

## Frame times

Headless Chromium with software rendering (no GPU), Tổng quan, desktop 1440×900, median of 3 runs. The comparison
is HEAD before this work against the new code, with the same server and the same scripted assistant burst (8 tool
steps, 20 text events, an answer):

| Graph | Idle mean | Idle p95 | Burst p95 |
|---|---|---|---|
| Real — before | 16.68 ms | 16.8 ms | 33.4 ms |
| Real — after | 16.69 ms | 16.7 ms | 33.3 ms |
| 3× — before | 17.23 ms | 16.8 ms | 50.0 ms |
| 3× — after | 16.68 ms | 16.8 ms | 33.3 ms |

The core adds no frame cost when idle. On the real graph a burst costs the same as before. On the 3× graph it is
faster (worst frame 283 → 117 ms), because the folded graph draws fewer nodes and edges, and the routes are
computed once per layout. Measured after the last fixes (partial groups, label sides, repayments on a group).

## Gaps and trade-offs

- **Opening a group can move money in and out.** When the half of the ring a group sits on cannot hold it, money
  in and out leave their sides (screenshot SCR-CL-12-group). It happens only on that explicit click, and “Thu gọn”
  puts them back. Keeping them pinned would have meant folding the group again at once.
- **A partly opened group cannot be opened further on the graph.** Its “+n khác” node says so and lists the rest;
  Danh sách shows them all.
- **Small screens fold more.** On the demo client's Tổng quan at 1440×900, three classes, the two debts, four goals
  and two news items fold. Folded debts still repay on their group's edge.
- **Readability at zoom levels** was checked by eye (holdings' names show from 1.3×), not measured.

## Screenshots

- [Desktop, Tổng quan](../assets/current_ui/SCR-CL-12_desktop-dark.jpg) ·
  [phone, Tổng quan](../assets/current_ui/SCR-CL-12_phone-dark.jpg)
- [The core, dark](../assets/current_ui/SCR-CL-12-core_desktop-dark.jpg) ·
  [the core, light](../assets/current_ui/SCR-CL-12-core_desktop-light.jpg)
- [A 3× graph, folded](../assets/current_ui/SCR-CL-12-dense_desktop-dark.jpg) ·
  [a group opened by hand](../assets/current_ui/SCR-CL-12-group_desktop-dark.jpg)
- [A stream in flight](../assets/current_ui/SCR-CL-12-dataflow_desktop-dark.jpg) ·
  [a failed read](../assets/current_ui/SCR-CL-12-failed_desktop-dark.jpg)

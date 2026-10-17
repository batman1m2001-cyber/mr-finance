# The central wealth core and the graph's layout and routing — plan

Owner requests (2026-10-17):
- [`2026-10-17_central_wealth_core.md`](brd/sources/owner_requests/2026-10-17_central_wealth_core.md) (“Core”);
- [`2026-10-17_graph_layout_routing.md`](brd/sources/owner_requests/2026-10-17_graph_layout_routing.md) (“Layout”).

They become OWN-GW-20…32 ([owner_requirements.md](brd/requirements/owner_requirements.md)) and the FEAT-40 section
“The centre and the layout”. Work happens on branch `exp/graph-workspace`, served on :8040. There is no PR to main.

## 1. Audit — what exists (read and measured 2026-10-17)

The renderer is `web/workspace/graph.js` (660 lines): one SVG, nodes created once and moved by transform.
- **Layout (`layout()`, G8):** each kind has a fixed sector `[from°, to°, radius]` (`SECTOR`, overridden by
  `LAYOUT_BY_LENS` and `NARROW`). Nodes are spread evenly over their sector. A crowded sector (≥ 7 nodes, or
  goals, sources and scenarios) alternates between two radii, then `relax()` pushes overlapping discs apart for up to
  24 rounds.
- **Labels (`placeLabels()`):** each label takes the first free place (side, other side, below, above) clear of
  discs and earlier labels. Otherwise it is shortened, or hidden until pointed at (“quiet”). Labels ignore edges.
- **Edges (`curve()`):** every edge is one quadratic arc bent the same way, trimmed at the two discs. Nothing checks
  what lies under it.

The G8 measure counted only idle crossings and label overlaps. A stricter audit (`layout_audit.py`, the scratch
harness that becomes L0's test) counts, in screen pixels, on every lens, idle and with each node picked in turn:

| Real graph (21 nodes on Tổng quan) | discs overlap | labels overlap | label on a disc | edge through a node | edge through a label | crossings |
|---|---|---|---|---|---|---|
| desktop, idle (worst lens) | 0 | 0 | 0 | 3 | 7 | 0 |
| desktop, a node picked (worst) | 0 | 1 | 3 | 9 | 6 | 0 |
| phone, idle (worst lens) | 0 | 1 | 0 | 6 | 5 | 0 |
| phone, a node picked (worst) | 0 | 2 | 3 | 13 | 4 | 0 |
| **3× graph, desktop Tổng quan idle** | 0 | 0 | 0 | **38** | **17** | 0 |
| 3× graph, desktop Tổng quan, picked (worst) | 0 | 2 | 4 | **66** | 6 | 0 |

Why (from the audit's examples):
- **The two staggered rings.** A spoke to the outer ring passes over the inner node beside it (ME → Bất động sản
  through Tiền gửi, ME → Cổ phiếu through Vàng) and over its label.
- **Relations drawn as one fixed arc.** Source → class and class → risk edges cut straight through “My Wealth”
  (`SR:tcbs > CL:stock thru ME`).
- **Too much for the arc.** A pick opens holdings or relations into a sector that is already full, so labels land
  on discs. The 3× graph puts 50 nodes on arcs sized for 20.

The centre is a 62 px disc: a two-stop radial gradient (`#ws-me`), a drop-shadow filter, four text lines, and an
activity ring shared with every node (`act`, `writing`, `hit`). It has no layers, no ambient motion, and no tie to
the money sparks (which already run on every money edge: CSS `ws-money` on `stroke-dashoffset`, timed per edge).

Studio (`operonx_studio/static/canvas.js` `dfComet`, `studio.css`) animates wires with dash offsets on one CSS
clock. The core reuses that clock (decision C3), so it adds no animation loop.

## 2. Decisions — layout and routing

1. **One ring, exclusive slots.** Every node joined to “My Wealth” sits on one ellipse fitted to the canvas, one
   node per slot. Nothing sits between a ring node and the centre, so a straight or gently curved spoke never
   crosses a disc. The staggered rings and `relax()` go: they caused the spokes through nodes.
2. **Group order, fixed and shared by all lenses.**
   - Clockwise from the right: money out at 0°, then risks, policy, news, scenarios, goals, the reserve, and data
     sources in the lower arc.
   - Money in sits at 180°.
   - The assets fill the upper arc, then the debts (back toward money out).
   - Money in and money out are pinned when both show. Otherwise the ring is rotated so the assets' middle is at the
     top.
   - Inside a group, the order is by value (largest first), then by id.
   - A group gap is 2.5× a slot gap.
3. **Slots from the labels, along the arc.**
   - A slot's width is the tangential room its node needs at its angle. On the sides, the label sits beside the node,
     so the slot needs only the label's height. At the top and bottom, the label is centred on the node, so the slot
     needs the label's width. Width is estimated from the characters, as now.
   - Positions are laid out along the ellipse's arc length, from a table built once per draw, so gaps are in pixels.
   - Two passes: the angle decides the label's side, and the side decides the slot.
   - The ellipse is the largest one that leaves label room outside it: one line of width at the sides, two lines of
     height at the top and bottom. In a holdings lens it also leaves a band for the fan of holdings.
4. **Fold, do not squeeze (progressive reveal).**
   - If the slots need more arc than the ring has, the lowest-value member of the group with the most demand per
     member folds into a group node, “+n tin tức” or similar. This repeats until the slots fit.
   - The group node is an ordinary node of kind `group`. It carries its members' count, focus keys and records, and
     the sum of their values where the sum means something (it does not for goals or scenarios).
   - Never folded: “My Wealth”, money in and out, the reserve, the selected node, and a group the person opened.
   - Clicking a group node opens it, and another group may fold to make room. An opened group shows a small
     “Thu gọn” node at its end.
   - Activity keyed to a folded member (`run`, `light`, `keep`) lands on its group node, so assistant events never
     change the layout.
5. **Branches.** In the Tài sản lens, an opened class gets a slot as wide as its holdings' fan. Its holdings sit on
   an outer arc behind it, in the band decision 3 keeps, with their names shown on zoom or on demand as now. The
   others keep their order and slide. Sources are a group on the ring; their edges to classes are relations.
6. **Routing with a check.**
   - One function, `route(e)`, returns a path. It is cached per layout, and labels and drawing use the same one.
   - Spoke: from the centre's rim to the node's inner side, with a bend of at most 8 % of its length.
   - Relation: the first candidate that passes the check, in this order:
     1. an inward cubic, both ends leaving toward the centre;
     2. the same cubic bent round “My Wealth” on the left;
     3. the same, bent on the right;
     4. a path that travels inside the ring at a fixed depth.
   - The check samples every 6 px along the path. It fails if a sample falls within (radius + 3 px) of a disc that is
     not an end, within the centre's aura, or inside a placed label.
   - A node's relations share their first control point (one trunk that splits).
   - Holdings leave their class on its outer side.
7. **Labels clear of edges.** `placeLabels()` treats the spokes' samples (known from decision 6 before drawing) as
   obstacles too. Relations drawn later are routed around the placed labels (decision 6), so neither crosses the
   other.
8. **Edge emphasis (OWN-GW-29).**
   - Money: as now.
   - Holdings and class spokes: stroke opacity .45.
   - Derived summaries: .3 and dashed.
   - Hypotheses: dotted.
   - With a pick or a focus, the edges not on the active path drop to .08.
   - Relations show only on demand, as now.
9. **Exploration (OWN-GW-30).**
   - A **Tập trung** button beside the zoom buttons, enabled when a node is picked. It fits the view to the selection,
     its neighbours and their labels (zoom at most 1.8), with everything else still drawn and dimmed. “Vừa khung”
     returns.
   - Group nodes open and close (decision 4).
   - Keyboard: `f` focuses, `0` fits.
10. **Stability (OWN-GW-31).**
    - The layout depends only on the lens, the visible set, the opened classes and groups, and the canvas size.
    - A pick that opens nothing moves nothing.
    - Assistant events never re-layout.
    - Positions are tweened by the existing transform transition, so a change is seen as a slide.

## 3. Decisions — the core

1. **Layers in the existing SVG, gradients only.** Back to front:
   - aura: a radial gradient from accent to transparent, out to r + 30;
   - two hairline concentric rings at r + 10 and r + 18;
   - bezel: a 1.5 px ring with a vertical gradient, light at the top, as a rim light;
   - body: a radial glass gradient, a lighter violet high, deep navy at the edge, 92 % opaque;
   - inner light: an ellipse low in the body, cyan-violet, low opacity;
   - top highlight: a white-to-transparent ellipse at 18 %;
   - a fine inner tick ring;
   - face: a darker disc under the figures, so the value keeps ≥ 7:1 contrast;
   - figures.

   Colours are CSS custom properties on `stop-color`, with light and dark values. The `drop-shadow` filter on the
   centre goes: the aura replaces it.
2. **Ambient motion, transform and opacity only (FEAT-33).**
   - The aura and the inner light breathe together: opacity, 7 s, ease-in-out.
   - One hairline ring drifts out from the rim and fades: scale 1 → 1.22, 9 s, with a second ring half a period
     behind.
   - Nothing rotates.
3. **Synced with the money, on the sparks' own clock.** `sparks()` already knows each money edge's period
   (`dur / n`) and when a head reaches the end (`dur · len / (len + SPARK_LEN)`). When a money edge touches
   “My Wealth”, `drawEdges` adds a **port**: a short rim arc at the attachment angle.
   - The port runs a CSS opacity keyframe with that period. Its phase is the arrival time (income, into the core) or
     the departure time (spending and repayments, out of it).
   - The port is created in the same frame as the sparks, so they share the document timeline.
   - Income ports also drive a **band**: a soft gradient strip across the body, rotated from the in-port toward the
     out-port, lighting at each arrival.
   - No JavaScript runs per frame.
4. **Assistant activity.**
   - `busy` (a tool running): the bezel takes `--pulse`, and the aura breathes at 1.6 s.
   - `writing()` (each text event): one ripple, a tracked Web Animation (transform and opacity), at most one every
     350 ms.
   - `arrive("ME")`: one bezel flash.
   - These replace the shared ring classes on the centre only.
5. **States.**
   - Idle.
   - `sel`: a crisp accent ring at r + 4, and the aura steady and brighter.
   - `busy`, `writing`: as above.
   - `flow`: a money edge or flow node is pointed at or picked. That port and its sparks go to full, the others step
     back, and the band tints toward the flow's colour.
6. **Figures.** Static: no animation or filter, tabular numerals, the face behind them. They stay buttons with
   “Cách tính”.
7. **Reduced motion.** No breathing, ripples, ports or band motion: the aura is static at its mean. `busy` and
   `writing` become a still `--pulse` bezel.

## 4. Phases

| Phase | What | Gate |
|---|---|---|
| C0 | BRD: the two sources, OWN-GW-20…32, FEAT-40 section, this plan | `scripts/check_brd_docs.py` 0 errors |
| L0 | The audit as a test, `tests/ui/test_graph_layout_ui.py`: every lens on desktop and phone, idle and a pick of each kind, the real graph and a 3× graph; a stability check (positions before and after a pick and an answer) | runs; fails today with the numbers in §1 |
| L1 | Ring: group order, slots from labels along the arc, two passes, pinned flows, adaptive ellipse; labels outward and clear of spokes | L0 idle: 0 overlapping discs or labels, 0 labels on discs, 0 edges through nodes or labels, desktop and phone, real graph |
| L2 | Folding and branches: group nodes (kind `group`, keys, sum, open and close, activity mapped), holdings' fan in the band, sources as a group | L0 picks and the 3× graph at 0 on the same counts; picking outside Tài sản moves no node; an answer moves no node; lens switches keep the ring's order |
| L3 | Router: `route(e)` with the check, trunks, ports by side; edge emphasis | L0 with relations shown (every pick): 0 edges through nodes or labels; visible crossings 0 on the real graph |
| L4 | Exploration: Tập trung, keyboard `f`/`0`, group open and close from the inspector and the canvas | UI test: focus fits the selection with the rest visible; Vừa khung returns |
| C1 | The core's layers and theme tokens; the figures' face; filter removed | screenshots desktop and phone, dark and light; value contrast ≥ 7:1 measured |
| C2 | The core's motion: breathing and drift, ports and band on the sparks' clock, assistant states, `flow`, reduced motion | UI test: a port's peak within one frame of its spark's arrival; states toggle on the real events; nothing animates under reduced motion; idle frame mean and p95 within 1 ms of before (real and 3×) |
| V | Full suite; audit before and after (real and 3×, desktop and phone); frame times; FEAT-40 as built, matrix OWN-GW-20…32, report, CHANGELOG, screenshots SCR-CL-12 | OWN-GW-20…32 implemented_verified |

## 5. Out of scope

- A general graph-layout library (ELK, dagre, d3-force). The ring with slots, folding and a checked router covers
  the shapes this graph has, at this size. It stays in the existing renderer (owner: “reuse the current stack where
  practical”).
- Edge bundling across different nodes' relations, since relations show on demand, one node at a time.
- WebGL or canvas rendering. SVG holds the 3× graph within the frame budget (G10).

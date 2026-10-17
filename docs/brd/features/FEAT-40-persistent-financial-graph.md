# FEAT-40 — Persistent financial graph (the Customer's workspace)

| | |
|---|---|
| Type | Extension (owner request, 2026-10-17), **experiment**: branch `exp/graph-workspace`, its own public link; `main` and the live demo unchanged |
| Requirements | OWN-GW-01…14; keeps every requirement the Customer screens carry today (capability map below) |
| Users | Client (Customer role). RM and the staff roles keep today's shell and pages |
| Entry points | [SCR-CL-12](../ux/screens/client.md#scr-cl-12--không-gian-tài-chính-graph-workspace); `POST /api/overview` (extended), `POST /api/assistant/stream` (new) |
| Plan | [docs/GRAPH_WORKSPACE_PLAN.md](../../GRAPH_WORKSPACE_PLAN.md) G0–G7; decision [ADR-0035](../decisions/ADR-0035-the-customer-workspace-is-one-persistent-graph.md) |
| Status | see [traceability](../requirements/requirements_traceability.md) §5 |

## Behaviour (target)

### The workspace
- **One page, four regions:** the left toolbar, the graph in the centre, the right dock (Trợ lý · Thông tin) and the
  bottom strip. It is drawn once per session and per picked scope. Nothing navigates it away: a lens, a selection,
  a sheet or an assistant answer changes **view state**; the graph's DOM, pan, zoom, expanded classes and selection
  survive.
- **View state** is `{lens, sel, open, pan, zoom, sheet}`, kept per client and scope for the tab's life. The address
  carries the lens or the sheet (`#/client/xem/<lens>` for a lens; a sheet keeps its page's old address, e.g. `#/client/tin/do-thi/<event>`, and opens over the lens that page belongs to), so back and forward,
  reload and links work. A reload keeps the lens and sheet; pan and zoom start fitted.
- **Lenses** (toolbar, with tooltips; keyboard: arrow keys move, Enter picks): a lens sets which kinds are visible,
  which are emphasised, which classes open, the level of detail and the inspector's default content. It never
  refetches what the graph already holds.

| Lens | Visible and emphasised | Level of detail | Inspector default | Sheets it offers |
|---|---|---|---|---|
| Tổng quan | every kind except holdings and sources | overview | what moves the picture (events and policy by impact) | Toàn cảnh (SCR-CL-08), Chi tiết (SCR-CL-01) |
| Tài sản | asset classes opened to holdings, liabilities, data sources | holdings | totals and trust by source | Tài sản (SCR-CL-02) |
| Dòng tiền | income, expenses, liquidity and their flows; the month's figures on the edges | flows | the month: in, out, saved; the largest items | Dòng tiền chi tiết (Money Flow of SCR-CL-08) |
| Mục tiêu & kịch bản | goals and hypothetical scenarios, the classes funding them | goals | goals by status, scenarios offered | Kế hoạch (SCR-CL-03) |
| Tin & sự kiện | approved news events and policy items, the classes they may move | events | events by impact | Tác động thị trường (SCR-CL-05), Đồ thị tác động (SCR-CL-09), Chi phí chính sách (SCR-CL-06) |
| Rủi ro | risks (stress loss vs tolerance, concentrations, reserve), the classes behind them | risks | the risk figures against their limits | Khẩu vị rủi ro (SCR-CL-04), Chi tiết (SCR-CL-01) |
| Chuyên gia | — (a dedicated view, OWN-GW-05) | — | — | Chuyên gia (SCR-CL-07) |
| Bộ nhớ | — (a dedicated view) | — | — | Bộ nhớ (memory page) |

- **Sheets** are the existing page modules, rendered in a panel over the graph's area (the graph stays mounted,
  dimmed behind it). Closing a sheet returns to the same graph state. A sheet is used only for a workflow the graph
  cannot carry: forms, uploads, the risk questionnaire, the planning calculator, tables, the Sankey, the event path
  graph, the specialist contact, the memory page.

### The graph
- Built from `POST /api/overview` (FEAT-30), extended with three kinds, each with the records it was read from:
  - `flow` — **Thu nhập** and **Chi tiêu** of the last full month (actual transactions), each edge valued;
  - `liquidity` — **Thanh khoản dự phòng**: liquid assets and months of spending (always present, not only when
    low);
  - `scenario` — the stress tests and life scenarios the planning page offers (`GET /api/scenarios`); a scenario's
    effect is computed only when the person runs it from the inspector (`POST /api/scenario`, FEAT-26) and shown as
    hypothetical edges “nếu xảy ra”.
- **Certainty on every node and edge** (OWN-GW-12): `actual` (recorded holdings and transactions: solid line),
  `estimate` (market estimates, model forecasts, policy probabilities, news impact under the CIO's scenarios:
  dashed, wording “có thể ảnh hưởng”) and `hypothetical` (scenarios: dotted, a “giả định” badge). A legend names
  the three. The client sees only CIO-approved news events (FR-502); nothing unverified reaches the client's
  graph, and the legend says so.
- A scenario's value is never added to net worth or to any class; its edge points from the scenario to what it
  would move, labelled “nếu xảy ra”. Running a scenario (a sheet) changes no stored holding.
- Interaction (FEAT-30 kept): a node is a button (click, Enter, Space); selection lights its links and opens the
  inspector; a class opens to its holdings (double-click, `+`/`−`); the canvas pans (drag, arrow keys with focus on
  the canvas) and zooms (wheel, `+`/`−` buttons, “Vừa khung”); the list view is the same graph as rows (the
  accessible alternative; the default on a phone).

### The right dock
- **Trợ lý** — the assistant (FEAT-32), docked instead of floating, with its conversations, confirmations, cards,
  sources and memory links unchanged.
- **Thông tin** — the inspector: the selected node's figures with their “Cách tính” (BRD-NFR-11), its links with
  their records, “Mở rộng”, and the sheets that show it in full. With nothing selected: the lens's default content.
- The dock collapses to a rail; it remembers the last tab.

### The bottom strip
- The Toàn cảnh cards (net worth and month change, the month's cash flow with six months, allocation, stress loss
  vs tolerance, liquidity reserve), each with its “Cách tính”; a card focuses its lens. “Thu gọn” folds it to one
  line; the choice is kept.

### The assistant and the graph (OWN-GW-06…10)
- The workspace asks through `POST /api/assistant/stream` (same body as `POST /api/assistant`; served graph with
  doors, `Accept: text/event-stream`). Events, each sent when it happens:
  - `step` `{call_id, tool, label, state: "running"}` when a tool starts, with `nodes`: the graph kinds or ids the
    tool reads (from the registry, e.g. `dong_tien` → flow nodes);
  - `step` `{call_id, state: "ok" | "failed", ms, focus}` when it ends, `focus` = the keys the tool's result names;
  - `text` `{delta}` as the model writes (model mode only; the template mode sends the texts at the end);
  - `wait` when a write needs confirmation; `answer` with the same object `POST /api/assistant` returns; `error`.
- The graph answers each event and nothing else (refined by OWN-GW-17 below): a running tool's nodes pulse and the
  paths to them light; a finished tool's focus keys light; a streamed sentence that
  names a node (its focus key is in a finished step) lights it as the sentence arrives; the final answer's focus and
  citations stay marked until the next question; a failed step turns its nodes' ring red and the dock says what
  failed; a failed turn marks nothing and says so.
- Motion: transform and opacity only (FEAT-33's rule), particles as tracked Web Animations, at most a few at a time;
  paused in a hidden tab; reduced motion replaces pulses and particles with still outlines.

### Hierarchy and dataflow (refinement, OWN-GW-15…19)
Studied from the OperonX Studio data-flow view (`operonx_studio/static/canvas.js` `dfComet`, `studio.css` `.dflinks`,
`motion.js` `liveCanvas`):
- wires are silk, about 1 px at 55–75 % opacity;
- one spark per wire says which way the data goes;
- a picked lineage lights while everything else steps back to about 8 %;
- a card reacts when the data reaches it;
- particles are capped.

The Studio animates `stroke-dashoffset`. Here FEAT-33 allows only transform and opacity, so a pulse is a head and a
short trail of dots moved along the curve by transform, with an opacity flicker.

- **Three layers** (OWN-GW-15):
  - “My Wealth” is the anchor.
  - The second layer is what the lens is about: the asset classes, the money in and out, the reserve, goals, risks,
    news and scenarios.
  - The third layer is shown on demand. A class's holdings appear when it is selected (the Tài sản lens no longer
    opens every class). The sources stay a quiet outer ring without edges.
- **Spokes always, relations on demand.**
  - The edges between “My Wealth” and the second layer are always drawn.
  - The edges between two other nodes (news → class, class → policy or risk, source → class, class → holding) are
    drawn only in four cases: for the selected or pointed-at node, for a node the assistant is reading, for a path
    a pulse is taking, or for an answer's kept nodes.
- **Labels never overlap.** After layout, each label takes its first free place among: its side, the opposite side,
  below, above. A label with no free place is shortened.
- **Semantics** (OWN-GW-18):
  - **Money and holdings (actual):** a solid silk line with a small end knob at the receiving side (Studio's
    bouton). Its width follows the value.
  - **Estimates (news, policy):** dashed.
  - **Hypothetical (scenarios):** dotted, plus the “giả định” badge.
  - **A pulse means the assistant read data along that path. It never means money moved.** It wears the data colour
    (never the in/out money colours). On a hypothetical edge the pulse head is hollow. The legend says so:
    “Xung sáng: trợ lý đang đọc dữ liệu, không phải giao dịch”.
- **Events → motion** (OWN-GW-17). Each stream event is answered once, and nothing moves without an event:
  - **A tool starts:** its nodes' rings pulse, the paths from “My Wealth” to them light, and the graph enters focus
    (unrelated nodes and edges dim).
  - **A tool ends ok:** a pulse runs from each of its nodes back to “My Wealth” (the data reaching the answer), and
    “My Wealth” reacts when it arrives. For news and policy the path has two hops: the item, then the class it
    affects, then “My Wealth”.
  - **A tool fails:** its nodes and paths turn red. No pulse runs, because no data came back.
  - **Text arrives:** “My Wealth” shows it is writing, as long as text keeps coming.
  - **The answer completes:** what it named stays lit, with its paths, and the rest stays dimmed until the next
    question or a click on the background. A failed turn marks nothing.
- **Performance** (OWN-GW-19):
  - no edge animates on its own, and a pulse runs only after an event;
  - at most 8 pulses at once (4 elements each), as tracked Web Animations, paused in a hidden tab;
  - no pulses or flicker under reduced motion, where lit paths and rings stay still;
  - measured on a graph three times the demo client's size.

**Money in motion** (owner, 2026-10-17). Every real money edge always carries Studio's spark (canvas.js `dfComet`):
short beads of light with a crackle trail, sliding at 210 px/s the way the money goes. Income runs into “My Wealth”
(blue), spending runs out (orange), and this month's repayments run out along the debt they pay down (`repaid` on
the loan and card edges, from the month's spending categories). Bigger flows carry more beads. An estimate or a
scenario never runs. Reduced motion hides them. This is the one keyframe that is not transform or opacity
(`stroke-dashoffset`): idle frames were measured equal with and without it (16.7 ms mean, p95 16.8 vs 16.7 ms).

### The centre and the layout (OWN-GW-20…32)
Plan: [`docs/GRAPH_CORE_LAYOUT_PLAN.md`](../../GRAPH_CORE_LAYOUT_PLAN.md). Replaces the sectors, the two staggered rings
and the free relaxation of G8, which the audit showed still drew spokes through other nodes and their labels.

**Layout** (OWN-GW-26…28, 30, 31):
- **One ring, one node per slot.** Every node joined to “My Wealth” sits on one ring fitted to the canvas, with no
  other node between it and the centre. A spoke therefore never passes through a node. Labels sit outside the ring,
  so a spoke never crosses a label.
- **Groups in a fixed order.** Money in sits at the left, money out at the right. The upper arc holds the assets,
  then the debts (next to money out, where repayments go). The lower arc holds risks, news and policy, scenarios,
  goals and the reserve; in the Tài sản lens, also the data sources. Gaps between groups are wider than gaps inside a
  group. The order is the same in every lens, so a node keeps its place relative to the others.
- **Slots sized from the labels.** Each slot is the room the node's disc and label need at its place on the ring:
  beside the node on the sides, above or below it at the top and bottom. Slots are measured along the ring in
  pixels. The ring is the largest that leaves the labels room on the canvas.
- **Less, not smaller.** When the slots need more ring than there is, the smallest items of the most crowded group
  fold into one group node, “+n …”. It carries their count, their focus keys and their records. A click opens it.
  The selected node, money in and out, and the reserve never fold. The assistant's events on a folded item go to
  its group node, so an answer never moves the layout.
- **Branches on demand.** A class picked in the Tài sản lens takes a wider slot, and its holdings fan out behind it.
  The other nodes slide along the ring in the same order.
- **Routing.** Spokes run from the centre's rim to the node's inner side, gently curved. Relations (news → class,
  source → class, class → risk) are shown only on demand. Each one leaves its node on the inner side and is routed
  clear of “My Wealth”, of every other disc and of every label: the first clear route among an inward curve, a curve
  bent round the centre on either side, and a path along the inside of the ring. A node's relations leave together
  as one trunk that splits. Holdings leave a class on its outer side.
- **Readable connections** (OWN-GW-29). Money: solid, width by value, with sparks. Holdings and class spokes: thin
  silk. Summaries of news, policy and risk: fainter and dashed. Hypotheses: dotted. With a pick, only the picked
  node's edges stay strong; the rest drop to a trace.
- **Exploration** (OWN-GW-30). Fit, zoom and pan, as before. **Tập trung** zooms to the selection and its neighbours,
  with the rest still visible and dimmed. Group nodes open and close.
- **Stable** (OWN-GW-31). Selecting a node outside the Tài sản lens moves nothing. An answer moves nothing. A lens
  switch keeps the order around the ring.

**The centre** (OWN-GW-20…25), drawn in the same SVG with gradients only (no blur filter on anything that moves):
- **Layers, back to front:** a soft aura; two thin concentric rings; a bezel lit from above (rim light); a deep
  glass body; an inner light; a top highlight; then a darker inner face under the figures.
- **Ambient motion:** the aura breathes slowly, and a thin ring drifts outward from the rim and fades. Nothing spins,
  and there are no particles.
- **Synced with the money.** Where each money edge meets the rim, a port lights as a spark arrives (income) or
  leaves (spending, repayments). Each income arrival also sends a soft band of light across the core toward the
  money out. All of this is timed from the sparks' own animation, on the same clock.
- **The assistant:**
  - while a tool runs, the rim takes the data colour and breathes faster;
  - while the answer streams, each text event sends one ripple from the rim;
  - when a pulse arrives home, the rim flashes once.
- **States:** idle, selected (a crisp accent rim), thinking, streaming, and flow (a money edge or flow node pointed
  at or picked: its port and sparks brighten, the core's inner band tints toward that flow).
- **Figures:** the net worth and its two lines sit on their own darker face, never animated or filtered, in tabular
  numerals. They stay buttons with “Cách tính”, readable in both themes.
- **Reduced motion:** no breathing, ripples or port pulses. The thinking and streaming states become a still rim in
  the data colour.

**As built (2026-10-17, `web/workspace/graph.js`, `web/core/tokens.css`):**
- **The ring is a rounded square** (a superellipse, exponent 2.7), not an ellipse: it is still convex, so a spoke
  meets nothing before its node, and its corners hold nodes an ellipse would waste on a wide canvas.
- **Slots come from the measured labels** (canvas text width, the CSS font sizes), projected on the ring's direction
  at each place. Above or below a node a long name wraps onto two lines (14 characters on desktop, 11 on a phone).
  Overlaps found after a pass widen the slots between the two items by the overlap's depth. A spoke that would touch
  another node's disc or label widens them too. The ring shrinks until every label is on the canvas.
- **What folds first:** the group taking the most ring per member, weighted: data sources, news and policy fold first,
  assets last, and money in and out and the reserve never. The lens's own subject folds last (the news on Tin, the
  goals on Mục tiêu, the classes on Tài sản). While money in and out are
  pinned to the sides, only groups on the crowded half fold. Folded debts still repay on their group's edge.
- **Opening a group** shows its members and a “Thu gọn” node, and is remembered per lens. If its half cannot hold
  it, the flows leave their sides (closing the group puts them back). If the whole ring still cannot hold it,
  groups opened earlier fold again. If even that is not enough, the group opens partly: its largest members show,
  and the rest stay behind “+n khác” (“không đủ chỗ để mở hết”, all of them in Danh sách). Labels are never squeezed
  onto discs to make room.
- **An open class's label** takes the first side clear of its holdings and its own spoke, along the ring first. At
  a corner of the ring, the side it points to is where a holding fans out.
- **Routes** are checked against every disc (the centre's with its aura) and every label box. A relation takes the
  first clear route: an inward curve, then curves bent round the centre on either side, then a path along the
  inside of the ring. If none is clear, it takes the least crossed.
- **The core** is SVG gradients and CSS opacity and transform only. Each money edge runs one, two or three sparks
  per 0.9 s beat. Its port peaks on the beat. The band crosses on the income's arrival, and the out-flows leave
  0.36 s later. Streaming ripples are Web Animations, at most one per 350 ms.
- **Tập trung** is a toolbar button (enabled once something is picked) and the key `f`; `0` fits the whole graph.

### Money flows, scenarios and the assistant (OWN-GW-33…50)
Plan: [`docs/UNIFIED_FLOWS_PLAN.md`](../../UNIFIED_FLOWS_PLAN.md) (decisions F1–F12). The graph becomes one money
model: what really moved, what the CIO's assumptions estimate, and what the person supposes.

- **Three certainties and a family mark** (OWN-GW-38).
  - **Actual:** a record.
  - **Estimate:** computed under the CIO's assumptions (news, policy, a goal's monthly need).
  - **Hypothetical:** a scenario.
  - A holding or category owned by another family member carries a person mark.
  - Nothing hypothetical is added to net worth or shown as a done transaction.
- **Money edges** (OWN-GW-34…37). Each money edge carries its amount, its monthly rate and its direction:
  - income and spending, and this month's categories on demand;
  - repayments;
  - each goal's monthly need;
  - each news event's 3-month change per class;
  - a policy item's impact where it touches one class;
  - an active scenario's change per class and its extra yearly costs.

  Every other edge is a relation, with no sparks.
- **Goals share their pool** (OWN-GW-36, 49). When followed goals count the same liquid pool, the graph and
  Thông tin say so once and total the monthly needs against the surplus.
- **Scenarios together** (OWN-GW-39, 40). One engine combines the active scenarios:
  - shocks compound per holding;
  - each change is attributed in proportion;
  - a shared cost counts once;
  - liquidity, the surplus and the goals are recomputed on the shocked picture.

  A bar shows what is active and the net worth “nếu xảy ra”. The person can add their own what-if (property,
  stocks, gold, floating rate, income).
- **Motion from money** (OWN-GW-41, 48). Sparks per beat, trail, speed and opacity follow the monthly rate against
  this month's larger flow, within limits. A one-off (policy, scenario) is relative and capped at half. Treatments:
  - actual bright;
  - estimate dashed;
  - hypothetical hollow and dotted.

  Off screen, everything sleeps.
- **Select an edge** (OWN-GW-46). Thông tin shows its ends, amount, certainty, sources, Cách tính, assumptions,
  confidence where recorded and downstream effects.
- **The assistant sees the graph** (OWN-GW-42, 45, 47). It is told the selection and the active scenarios. It can
  list a node's links (`lien_ket`) and compare or combine scenarios (`so_sanh_kich_ban`). The graph lights what
  each tool read.

**As built (U1–U5, 2026-10-17).** Report: [unified_flows_report.md](../testing/unified_flows_report.md).
- **Categories open on Dòng tiền only.** Picking income or spending fans out the month's categories there.
  Tổng quan keeps its ring still, because a pick there must move no node (OWN-GW-31).
- **The strip has no goal line.** The plan put the goals' monthly total on the strip. That line cost 38 px of
  graph height on every lens, and goals folded on Mục tiêu, so the total sits in Thông tin instead (“Các mục tiêu
  cần … / bạn dư …”).
- **The selection's label reaches a model only.** In template mode (no model) the instructions get the
  selection's kind, not its name.
- **The two graph tools are model-mode tools.** The keyword fallback keeps the Copilot's 13 tools and does not
  route to `lien_ket` or `so_sanh_kich_ban`.
- **A comparison names every goal's status.** The picked goal comes first, so “this goal” has an answer.
- **An active scenario sits on its own spoke.** At rest the spoke carries its whole change (class shocks and
  costs), moving in hollow dots. Its fan of class and cost edges shows when it is picked or read, as a news item's
  does. Drawing the fan all the time cut across the ring (27 crossings, V audit).
- **Another member's holdings are marked on the graph.** In Gia đình, their initial sits on the rim (a shared
  category shows how many people share it), named on hover. There is one core, the family's total.
- **An active scenario's read pulses along its edges.** When a tool reads an active scenario, it pulses along
  that scenario's three largest hypothetical edges, then home, hollow.

## Feature map — every BRD feature and its graph form (OWN-GW-33, 50)

The Customer's graph is one model. Each BRD feature draws something on it, feeds what it draws, or stays a staff
tool or a dedicated view. A staff tool reaches the Customer only through what is approved: the CIO's approval is
still the gate.

| Feature | Graph form on the Customer's workspace | Certainty | Elsewhere |
|---|---|---|---|
| FEAT-01 News ingestion | None directly: an approved, applied item becomes an event node (FEAT-08) | — | CIO inbox (staff) |
| FEAT-02 CIO inbox and events | None until approved: then the event node | — | staff |
| FEAT-03 Research and regulation notes | None directly | — | staff |
| FEAT-04 CIO agent | None: its views reach the graph only through an approved run | — | staff |
| FEAT-05 Challenger | None | — | staff |
| FEAT-06 View decisions | The approval that lets an event onto the graph | — | staff |
| FEAT-07 Scenario engine and factor model | Each event → class edge's 3-month change; its P10/P90 is the edge's “Độ tin cậy” | estimate | sheet Tác động thị trường |
| FEAT-08 Application runs | Event nodes on Tin & sự kiện; the run is the edge's “Nguồn” (Lần áp dụng tin) | estimate | RM list |
| FEAT-09 Number trace | “Cách tính” on every node and edge (the formula from `/api/how`) and the trace in Thông tin | — | sheet Đồ thị tác động |
| FEAT-10 Goal branch | None (gap): its goal matches are the RM's tasks | — | RM, research page |
| FEAT-11 Audit log | None: edge sources name the records; the log stays staff | — | Compliance |
| FEAT-12 Roles | Only the Customer gets the workspace; staff keep their layout | — | — |
| FEAT-13 Impact by role | The family scope (person marks) and this family's event edges | estimate | RM list |
| FEAT-14 Versioned configuration | None: the assumptions an edge names come from it | — | staff |
| FEAT-15 Agent catalogue | None | — | staff |
| FEAT-16 Policy agent | Policy nodes (“Chính sách”) on Tin & sự kiện | estimate | staff radar |
| FEAT-17 CIO newsletter | None | — | staff |
| FEAT-18 Accuracy tracking | None | — | staff (Mô hình) |
| FEAT-19 External AI inbox | None | — | staff |
| FEAT-20 Consolidation | Holdings under their classes (open a class), source nodes on Tài sản, person marks for family members | actual | sheet Tài sản |
| FEAT-21 Dashboard | The core's net worth, the bottom strip | actual | sheet Chi tiết |
| FEAT-22 Statement reading | Source nodes on Tài sản; a read statement adds holdings | actual | sheet Tài sản (upload) |
| FEAT-23 Chat declaration | As FEAT-22, through the assistant | actual | the dock |
| FEAT-24 Risk test | Rủi ro lens: the stress-loss node (RK:drawdown) | estimate | sheet Khẩu vị rủi ro |
| FEAT-25 Policy-cost alerts and house views | Policy nodes, with an amount where the item touches one class | estimate | sheet Chi phí chính sách |
| FEAT-26 Life scenarios, stress tests, goals | Goal nodes with their monthly need, sharing one pool; stress scenarios combined (F4) in the bar; the person's what-if | estimate (goals), hypothetical (scenarios) | sheet Kế hoạch |
| FEAT-27 RM approval queue | None: a Customer's action goes to it from Kế hoạch | — | staff |
| FEAT-28 Specialist team | None | — | sheet Chuyên gia |
| FEAT-29 Pulse, Wealth Map, Money Flow | Pulse → the strip; Wealth Map → the graph; Money Flow → Dòng tiền with categories | actual | sheet Toàn cảnh |
| FEAT-30 Intelligence graph | The graph itself (news → class → family) | estimate | sheet Đồ thị tác động |
| FEAT-31 Intelligence Feed | Tin & sự kiện; the inspector's list | estimate | sheet Toàn cảnh |
| FEAT-32 Copilot | The dock; its stream lights the graph; it reads the selection and the scenarios (F10) | — | — |
| FEAT-33 Living interface | Answer focus keys light nodes and edges | — | sheets |
| FEAT-34 Header search and notifications | A result opens its lens or sheet | — | header |
| FEAT-35 Market data layer | None directly: it feeds the factor model behind the event edges | — | staff |
| FEAT-36 Alerts and central log | None | — | staff |
| FEAT-37 Conversations and memory | The goals the person follows decide which goal nodes show | — | sheet Bộ nhớ |
| FEAT-38 Knowledge and web search | None: answers cite their sources in the dock | — | the dock |
| FEAT-39 Background agents | None | — | sheet Bộ nhớ |

## Capability map — every Customer capability and where it goes (OWN-GW-11)

| Today (screen · route) | Capability | Requirements | In the workspace | Interaction model |
|---|---|---|---|---|
| SCR-CL-08 Toàn cảnh · `tong-quan/toan-canh` | four Pulse cards | KIT-UX-01 | bottom strip | metrics, a card focuses its lens |
| | Money Flow (Sankey) | KIT-UX-03 | Dòng tiền lens (flows in the graph) + sheet “Dòng tiền chi tiết” | graph + dedicated view |
| | Wealth Map | KIT-UX-02 | the graph itself (classes, holdings) | graph |
| | Intelligence Feed | KIT-UX-05 | Tin & sự kiện lens, inspector list; sheet Toàn cảnh | inspector |
| SCR-CL-11 Bản đồ tài chính · `tong-quan/ban-do` | overview graph, kinds, expand, node → page, list view | KIT-UX-04, OWN-UI-04 | replaced by the workspace graph (its behaviour kept, list view kept) | graph |
| SCR-CL-01 Chi tiết · `tong-quan/chi-tiet` | net worth hero, sources, allocation, P&L, risk, reserve, cash-flow forecast, headline news | BRIEF-DASH-01…07, DATA-04/05 | sheet “Chi tiết” (from Tổng quan and Rủi ro) | dedicated view (unchanged) |
| SCR-CL-02 Tài sản · `tai-san` | statement upload, chat declaration, holdings table | BRIEF-DATA-01…05 | Tài sản lens + sheet “Tài sản” | dedicated view for the forms and table |
| SCR-CL-03 Kế hoạch · `muc-tieu/ke-hoach` | goals, stress tests, assumptions, actions to the specialist queue | BRIEF-SCEN-01…03, FR-603 | Mục tiêu & kịch bản lens + sheet “Kế hoạch” | graph (goals, scenarios) + dedicated view (calculator, queue) |
| SCR-CL-04 Khẩu vị rủi ro · `muc-tieu/khau-vi` | the risk questionnaire and its limit | BRIEF-RISK-01…05 | Rủi ro lens + sheet “Khẩu vị rủi ro” | dedicated view |
| SCR-CL-05 Tác động thị trường · `tin/thi-truong` | hero, fan chart, contributions, events, goal notes, timeline | BR-08, BR-10, FR-502, CONTENT-01/02, NFR-11 | Tin & sự kiện lens + sheet | graph (events → classes) + dedicated view |
| SCR-CL-09 Đồ thị tác động · `tin/do-thi` | event path graph | KIT-UX-04, KIT-UX-06 | sheet from an event's inspector (“Xem đường đi của tin”) | dedicated view |
| SCR-CL-06 Chi phí chính sách · `tin/chinh-sach` | wealth check, policy cards, house views | BRIEF-IMPACT-*, ALERT-* | Tin & sự kiện lens (policy nodes) + sheet | graph + dedicated view |
| SCR-CL-07 Chuyên gia · `chuyen-gia` | specialist contact, team, queue (read-only) | BRIEF-FLOW-02 | Chuyên gia (sheet) | dedicated view (allowed, §3) |
| Bộ nhớ · `bo-nho` | memory items, conversations, documents | OWN-AS-12…15 | Bộ nhớ (sheet); the dock's links | dedicated view |
| SCR-CL-10 Copilot panel | the assistant | FEAT-32, OWN-AS-*, OWN-MOTION-* | right dock “Trợ lý” | docked panel |
| Header | search, notifications, scope switch, theme, sign-out | OWN-UI-03, FEAT-34 | top bar (kept); a page result opens its lens or sheet | unchanged |
| FEAT-33 | answer marks its evidence | OWN-MOTION-01…06 | marks graph nodes as well as sheet elements | unchanged keys |

Every old address still resolves: `tong-quan/toan-canh` → Tổng quan, `tong-quan/ban-do` → Tổng quan,
`tong-quan/chi-tiet` → Tổng quan + sheet Chi tiết, `tai-san` → Tài sản + sheet, `muc-tieu/ke-hoach` → Mục tiêu +
sheet Kế hoạch, `muc-tieu/khau-vi` → Rủi ro + sheet, `tin/thi-truong` → Tin + sheet, `tin/do-thi[/…]` → Tin + sheet
Đồ thị tác động, `tin/chinh-sach` → Tin + sheet, `chuyen-gia`, `bo-nho` → their sheets. So the assistant's
citations, the search and the bell keep working.

## Acceptance (OWN-GW-13)
- Lens switches keep the graph element, the selection, opened classes, pan and zoom (browser test).
- A sheet opens over the graph and closing it restores the same state; every old Customer route resolves to a lens
  and, where listed, a sheet that renders without errors.
- Selecting a node fills the inspector; the inspector's links select their node.
- A scripted assistant stream (no paid call) drives: running → pulse on the tool's nodes, finished → focus lit,
  answer → marks kept, failure → red ring and the failed step named; no animation without an event.
- Certainty: actual, estimate and hypothetical edges are drawn differently; a scenario's value is in no total.
- Phone (390 px): the toolbar as a row under the header (with Trợ lý); graph first, list one tap away; the dock below the graph; a sheet in the graph's place, so the dock stays reachable; no horizontal scroll.
- Reduced motion: no pulse or particle animation runs; marks are still outlines.
- The full suite stays green; the BRD checker passes.

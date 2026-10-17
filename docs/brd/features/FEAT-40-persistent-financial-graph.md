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
- The graph answers each event and nothing else: a running tool's nodes pulse and a particle travels the edge from
  “My Wealth” toward them (Studio's live-run pattern); a finished tool's focus keys light; a streamed sentence that
  names a node (its focus key is in a finished step) lights it as the sentence arrives; the final answer's focus and
  citations stay marked until the next question; a failed step turns its nodes' ring red and the dock says what
  failed; a failed turn marks nothing and says so.
- Motion: transform and opacity only (FEAT-33's rule), particles as tracked Web Animations, at most a few at a time;
  paused in a hidden tab; reduced motion replaces pulses and particles with still outlines.

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

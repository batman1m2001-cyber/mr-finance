# Changelog

Newest first. One line per meaningful change: date — what — documents touched.

- 2026-10-26 — Any document to the assistant (owner): paste, attach or photograph a statement, receipt, bill or
  asset description; read once on the client model, a file alone routes itself, saved behind Xác nhận with every
  item and the total. Gate: 5/5 roughened documents read as written (US$0.0034), four screens. — ADR-0041, FEAT-42,
  owner_requirements DOC, requirements_traceability §5, FEAT-22, FEAT-32, huong-dan/chung, docs/OCR_PLAN.md
- 2026-10-25 — Business feedback 7 (owner): the RM's desk is Tổng quan (“Khách hàng đang quản lý”, the net worth
  coloured), no Hôm nay (contact log in Thông tin), the client picker inside the Khách hàng and Advisory performance
  sheets, no “Nội bộ” on the RM's sheets (BRD-RULE-SEC-03 narrowed). — OWN-FB-19…25, business_rules, FEAT-13,
  requirements_traceability, docs/BUSINESS_FEEDBACK_7_PLAN.md
- 2026-10-24 — Business feedback 6 (owner): the RM's and the CIO's desks reorganised (nested tabs, Decision board
  with the inbox in it, plain words on impact, Mô hình and AI to Admin), the client's impact bars by asset class, and
  no Compliance or Expert account (their duties the CIO's, four eyes kept). Planned. — owner_requirements FB,
  requirements_traceability §5, docs/BUSINESS_FEEDBACK_6_PLAN.md
- 2026-10-24 — The data room's eval (D5): 90 questions, 30 per role, gold answers from the database; Haiku 5.5
  89/90, p95 5.3 s, US$0.003 a turn; Sonnet 5.5 measured (15/15, US$0.06 a turn, no forced tool call), so Haiku
  stays; totals computed in SQL, the recount's result says not to guess why, one catalog ambiguity fixed. —
  OWN-DA-07, OWN-DA-08, requirements_traceability §0 and §5
- 2026-10-24 — Measuring the news agents (owner): each ingest run's funnel, status and sources, the days by
  collection time; the scenario agents' moves scored at 3d and 1w (precision, recall, direction, coverage, event
  recall), valued in VND on the simulated book, labelled simulated; cost per model call, never 0 when missing; the
  trial page in View A and View B with a drill-down per move. — owner_requirements EV, requirements_traceability §5,
  docs/AGENT_EVALUATION_PLAN.md
- 2026-10-24 — The data room wired in (D4): `truy_van` in the registry for the five roles with a room, with the
  role's catalog; three queries a turn; an audit row per query; “Cách tính” (SQL, rows, table, time), closed; the
  template with `client_ai` off; the re-count rule, and a question naming a number the last answer did not say must
  call a tool (`tool_choice`): the rule alone did not make Haiku 5.5 count again. — OWN-DA-03, OWN-DA-05…07,
  requirements_traceability §5
- 2026-10-24 — The data catalog (D3): what the assistant reads before it writes SQL, per role: every table and column
  of the room with its meaning, unit and allowed values, shared rules, the pages' definitions and 12–18 examples
  each; a test fails on an undocumented column and runs every example in its room. — OWN-DA-04,
  requirements_traceability §5
- 2026-10-24 — The data room (D2): `truy_van`'s SQL runs on TEMP tables built for the role and person (copies, not
  views: a CTE named like a view passed the authorizer as that view), read-only under the authorizer, 2 s, 200 rows
  with the total; 54 adversarial and positive tests. — OWN-DA-02, OWN-DA-03, requirements_traceability §5
- 2026-10-24 — Totals are counts (D1): the inbox page says 1.417 (was 300) and “40 / 1.417”; alerts, search,
  the CIO desk's Tin stage and the held-news tool count in the database. — OWN-DA-01, requirements_traceability §5
- 2026-10-24 — The assistant reads the data itself (owner): totals are counts; one tool, `truy_van`, a SQL
  `select` on role-scoped read-only views under SQLite's authorizer, with a catalog, "Cách tính", an audit entry
  and an eval gate; amends `Param`'s rule for that tool. Planned (D0). — ADR-0040, owner_requirements DA,
  requirements_traceability §5, docs/ASSISTANT_DATA_PLAN.md
- 2026-10-23 — The test book built (D2–D3): `scripts/make_santander_vn.py` matches the 6,500 Santander clients to
  SCF 2022 households and writes them in the fixtures' schema; all valued by `wealth.valuation`, Σ AUM 428,000 tỷ,
  share at TCB 35 %, 58.7 % with over half their wealth in one class; calibration in `data/calibration/`. Proposed.
  — ADR-0038, docs/CLIENT_DATASET_PLAN.md
- 2026-10-23 — The test book (Q-27): 6,500 Private clients, all Techcombank's, from Santander's TOP clients
  (behaviour), matched SCF 2022 households (make-up of wealth) and the owner's totals (≥ 25 tỷ each, Σ AUM 428,000
  tỷ); the demo's five families kept; D1's sampler run on the real file (6,500 drawn, all TOP; the first 1,000 a
  subset). The submission's 21 tỷ-at-TCB assumption raised (TO_DISCUSS D-04). Proposed. — ADR-0038, ADR-0005,
  requirements/open_questions.md (Q-18, Q-27), decisions/README.md, docs/CLIENT_DATASET_PLAN.md, docs/TO_DISCUSS.md
- 2026-10-23 — The Private palette (business feedback 5): gold #c8a45d marks the main action with dark-brown words;
  brown #59392c the ink of links, tabs and selections; light grey and sand surfaces; champagne in dark. Replaces the
  black-and-red reading of feedback 4. OWN-WN-11. — sources/owner_requests/2026-10-23_business_feedback_5.md,
  owner_requirements.md, requirements_traceability.md, ux/design_system.md
- 2026-10-22 — The colour tone (business feedback 4, after Techcombank Private; the owner: red and black, not
  painful): Techcombank red marks the main action only — a primary button, Hỏi trợ lý, the bell's count; the rest
  stays black, white and greys. OWN-WN-11. — sources/owner_requests/2026-10-22_business_feedback_4.md,
  owner_requirements.md, requirements_traceability.md, ux/design_system.md
- 2026-10-22 — Headline News (business feedback 3): Chi phí chính sách is News and Prediction, the first tab; Đồ thị
  tác động second; Tác động tin is no tab (its address stays: the bell's and the feed's evidence). OWN-WN-10.
  — ADR-0037, sources/owner_requests/2026-10-22_business_feedback_3.md, owner_requirements.md,
  requirements_traceability.md, ux/information_architecture.md, ux/screens/client.md, ux/screen_inventory.md, FEAT-25.
- 2026-10-22 — The client's menu by the bank's names (business feedback 2, nine items):
  - four sections: Wealth View (Wealth view · Dữ liệu chi tiết tài sản), Wealth Planning Advisor (Wealth planning
    advisor · Risk profile test), Headline News, Relationship specialist;
  - Dòng tiền and Rủi ro leave the menu (on Wealth view; the risk test is Risk profile test);
  - the graph is hidden from the client (no tab, search hit or assistant page; its own address kept, unlinked);
  - Wealth view opens on net worth and sources, cash flow second; every old address still opens its page;
  - the Wealth Check's ahead/behind line is green/red (every KPI's had been grey);
  - the assistant's pages, router and the user guide use the same names. OWN-WN-01…09.
  — ADR-0037, sources/owner_requests/2026-10-22_business_feedback_2.md, owner_requirements.md,
  requirements_traceability.md, ux/information_architecture.md, ux/screens/client.md, ux/screen_inventory.md,
  ux/user_journeys.md, FEAT-21, 24, 25, 28, 29, 40, docs/WEALTH_NAMES_PLAN.md, docs/huong-dan/khach-hang.md

- 2026-10-22 — One checklist of the agents (owner): eight parts that call a model, one name each, the three
  evaluations named. — docs/AGENT_CHECKLIST.md, docs/AGENT_CHECKLIST_PLAN.md

- 2026-10-20 — Money on the graph's edges and a node's timeline (owner: “move the money to the edge … with +/−”, “a timeline chart … by day / month / year”, “create data for years”):
  - every money spoke shows its signed change over Ngày · Tháng · Năm (Tháng = Tổng quan's month change);
  - an estimate's spoke shows its own figure in grey (owner);
  - a picked money node shows Diễn biến in Thông tin: chart and table, from 2021;
  - the history is generated by `scripts/make_history.py` into `data/history/`, labelled simulated;
  - `POST /api/timeline`.
  — FEAT-40, api_reference, regression_coverage, docs/NODE_TIMELINE_PLAN.md

- 2026-10-20 — UI/UX fixes after a 134-screenshot review (owner): a sheet's header keeps one line (title no longer three lines at 1440 px, ✕ no longer on its own line on a phone, tabs fade where they scroll); a phone's header is one row (search and the name row behind buttons; the page starts ~76 px higher); graph and chart labels break between words; Toàn cảnh cards, phone tables and the heatmap's “−0%” fixed; Bộ nhớ's file picker, Việc nền's job names, amounts under a million in nghìn (“+192 nghìn”), the CIO's bell counts high-relevance news; English headings Vietnamese-first, the feature's English name kept small. — docs/UX_FIXES_1020_PLAN.md, ux/design_system.md, ux/screens/client.md, ux/screens/rm.md, FEAT-21, testing/regression_coverage.md

- 2026-10-18 — Tài khoản và vai trò (owner's answer to Q-25: “do it”): Admin adds a staff account, changes a role, disables, enables or resets a password; one Admin files, a second approves, every step audited; an approved add or reset shows a one-time code once, redeemed on the sign-in page (`POST /api/auth/redeem`); disabling ends a live session at its next request; guards for one's own account, the last Admin, an RM with families, the demo's personas; the assistant files on a Xác nhận (`yeu_cau_tai_khoan`). OWN-MR-04 met. — open_questions.md Q-25, owner_requirements.md, requirements_traceability.md, screens/admin.md SCR-ADM-03, screens/shared.md SCR-SH-01, screen_inventory.md, role_desks.md, api_reference.md, FEAT-41, docs/MULTI_ROLE_UX_REPORT.md, testing/assistant/staff/*, docs/huong-dan/quan-tri.md

- 2026-10-18 — Việc nền (owner: “can our assistant control them?”): one page for the agents and the background jobs (CIO, Admin, Compliance; SCR-SH-02); the CIO runs Agent CIO and re-runs a failed challenger, Admin runs a job now (`POST /api/jobs/run`, one at a time, recorded, audited, alerted); the assistant does each on a Xác nhận (`chay_agent_cio`, `phan_bien_lai`, `chay_viec_nen`). — screens/shared.md, screen_inventory.md, role_desks.md, api_reference.md, sources/owner_requests/2026-10-18_owner_backlog.md, testing/assistant/staff/readiness.md, docs/huong-dan/*

- 2026-10-18 — The workspace fold is the same on every screen from 1440×900 up (owner: “4 mục tiêu khác” showed flat on a large screen): the fold is decided on the 1440×900 canvas's area, then drawn at the real size. — requirements_traceability.md OWN-GW-30, docs/OWNER_BACKLOG_1018_PLAN.md

- 2026-10-18 — Staff assistant stress test (owner request): each staff role's assistant tested as its users would use it — 54 conversations on the real model, a browser pass on every desk, the fallback per role; 14 S2 defects fixed (role duties in the prompt and the guide, the RM's book, agent_nen, every staff page openable, no pretended page-only decisions…), no S1; US$0.4858 of US$3. — testing/assistant/staff/*, requirements_traceability.md OWN-MR-10, docs/STAFF_STRESS_PLAN.md, docs/huong-dan/*

- 2026-10-18 — The floating Copilot button is gone (owner): the assistant is docked in every role's Trợ lý tab, its
  open/close mode and styles removed; Q-24 answered by the owner; Q-26 records what the BRD says of a specialist. —
  open_questions.md Q-24, Q-26; ux/design_system.md; docs/MULTI_ROLE_UX_REPORT.md §6

- 2026-10-18 — Multi-role UX M6 close-out: staff desks in the IA (`#/rm` is the book; Hôm nay at `#/rm/hom-nay`),
  journey J7, the regression record, seven real-model turns (US$0.0103), the final report; OWN-MR-08, 09, 11, 12
  verified (OWN-MR-04 stays partly met, Q-25). — information_architecture.md, user_journeys.md,
  testing/regression_coverage.md, matrix, features/README.md, docs/MULTI_ROLE_UX_REPORT.md
- 2026-10-18 — Fix (found by a real-model turn in M6 prep): the RM assistant's `so_khach_hang` was refused inside a
  signed-in served turn (the book read mapped every client's family through the checked read); now through the people
  table, never shown. Every desk tool is now tested signed in inside a served turn. — FEAT-41 §Acceptance, matrix
  OWN-MR-10
- 2026-10-18 — Multi-role UX M5: Compliance works at “Bàn kiểm soát” (experiment): every control as a lane with what
  waits at each step (held news, research, letters, policy documents, configuration, the chain), one queue oldest
  first, the alerts; Compliance's assistant with `ban_kiem_soat`. Every staff role now has its desk: OWN-MR-01, 06, 07,
  10 verified. — FEAT-41 §Compliance, screens/compliance.md SCR-CMP-06, screen inventory, ux/role_desks.md
  (Compliance built), matrix, api_reference, architecture/assistant.md, assets
- 2026-10-18 — Multi-role UX M4: the Expert works at “Bàn chuyên gia” (experiment): the queue beside the evidence —
  the picked recommendation's actions and the RM's note, the family's net worth, risk, liquidity, allocation and goals
  through the reads a specialist already makes (Q-26 applied), the certificate, approve / reject through the existing
  write; the Expert's assistant with `ban_chuyen_gia`, `ho_so_khach`; a desk's centre is inert under a sheet. — FEAT-41 §Expert, screens/specialist.md
  (SCR-SP-01 documented, SCR-SP-02), screen inventory, ux/role_desks.md (Expert built), matrix OWN-MR-05 verified and
  notes, open_questions Q-26, api_reference, architecture/assistant.md, assets
- 2026-10-18 — Multi-role UX M3: Admin works at “Vận hành” (experiment): Hệ thống's own read drawn as a map (sources →
  storage → AI → people, each node coloured by its last record), alerts, failing jobs, configuration waiting, people
  and roles (shown, not edited: Q-25), the chain; Admin's assistant with `van_hanh`, `chuoi_nhat_ky`,
  `cau_hinh_cho_duyet`. `GET /api/system` unchanged (factored into `system_read`). — FEAT-41 §Admin, screens/admin.md
  SCR-ADM-02, screen inventory, ux/role_desks.md (Admin built), matrix OWN-MR-04 (partly) and notes, api_reference,
  architecture/assistant.md, assets
- 2026-10-18 — Multi-role UX M2: the RM works at “Sổ khách hàng” (experiment): the RM's families as a relationship
  map by how soon they need the RM, sized by net worth; Hôm nay's calls, goal tasks, proposals, contacts; a family's
  pages open with the client picker set; the RM's own assistant with `so_khach_hang`. Badges now styled on desks;
  on a phone a sheet no longer widens to its row of tabs (Bản đồ tài chính drew its graph, not its list). —
  FEAT-41 §RM, screens/rm.md SCR-RM-07, screen inventory, ux/role_desks.md (RM built), matrix OWN-MR-03 (and notes
  01, 06, 07, 08, 09, 10, 12), api_reference, architecture/assistant.md, assets
- 2026-10-18 — Multi-role UX M0–M1: the CIO works at its desk “Bàn quyết định” (experiment): the news-to-family flow,
  the decision queue, exposure, events, model and agents from the existing stores; its 13 pages kept as sheets at
  their addresses; its own docked assistant with four desk tools. A 500 found on the way (a client on a route open to
  the specialist got a KeyError, not 403) fixed. — FEAT-41 §CIO, screens/cio.md SCR-CIO-15, screen inventory,
  ux/role_desks.md (CIO built), matrix OWN-MR-01, 02, 06…12, api_reference (`/api/desk`), architecture/assistant.md
- 2026-10-18 — Multi-role UX: plan and audit (owner request OWN-MR-01…12, experiment). Every staff role gets its own
  desk in the Customer workspace's frame, its pages kept as sheets at their addresses, and its own docked assistant.
  — docs/MULTI_ROLE_UX_PLAN.md, sources/owner_requests/2026-10-18_multi_role_ux.md, owner_requirements.md (MR),
  open_questions.md (Q-24…26), FEAT-41, ADR-0036 (supersedes ADR-0035 §1 for staff), ux/role_desks.md, screen
  inventory (SCR-CIO-15, SCR-RM-07, SCR-ADM-02, SCR-SP-01/02, SCR-CMP-06 proposed), matrix rows (planned)
- 2026-10-18 — "Dòng tiền tháng 9?" reads September 2026 (experiment). The model was not told the year: it asked for
  2025-09, outside the data (2025-10…2026-09), and the step failed. The prompt now carries today's date, and the cash
  -flow tool asks for the month alone unless a year is said (the latest such month with data). Real model: "tháng 9",
  "tháng 11" (2025-11) and "tháng 3 năm nay" all read. — src/assistant/turn.py, src/assistant/tools.py,
  src/assistant/progress.py, tests/test_assistant_stress.py
- 2026-10-18 — The Assistant panel says what it is doing while it works (owner: "display the progress… a message
  with clear semantic, concise… but don't be insecure", experiment).
  - A turn in flight is a short list. In order:
    - "Đang hiểu câu hỏi" (understanding the question);
    - each step in a sentence, then done, with its time ("Đã chạy kịch bản sốc: “VN-Index giảm 30%” · 0,1 s");
    - "Đang đọc kết quả để trả lời" (reading the results to answer);
    - "Đang viết câu trả lời" (writing the answer), with the words streaming below.
    It replaces a bare "Đang xử lý…" and step chips. Until now nothing showed between the tool's end and the
    answer's first words (~1.5 s).
  - The sentences are the server's (`assistant/progress.py`): two fixed ones per tool. The only details are the
    product's own names, a stress scenario's title or a YYYY-MM month. The person's text, ids, other arguments and
    results never show. A failed step says so ("Không thực hiện được: …").
  - Tests: tests/test_assistant_progress.py (new), tests/ui/test_assistant_panel_ui.py (the turn in flight).
    Screenshots: docs/brd/testing/assistant/progress/.

- 2026-10-18 — The assistant answers faster: hidden reasoning off (owner: "takes too much to respond", experiment).
  - Diagnosis: our code is ~0.1 s of a turn. The rest is the model: two calls on a tool turn, each reasoning first.
  - Same 26 conversations, in parallel on the same data: median turn 4.26 → 3.26 s (p90 7.50 → 5.26 s), first
    step or words 1.71 → 1.06 s, 11% cheaper.
  - Quality held after three changes that let tools, not the model, state figures:
    - the combined scenarios say over or within the drawdown limit;
    - the overview says the reserve's months;
    - the scenario tools name the preset levels.
    The panel drops the lead-in sentence the model now writes before a tool call.
  - Each turn's audit row keeps its timing (no words); `scripts/assistant_latency.py` reads it back.
  - Documents: docs/brd/testing/assistant/latency.md (new), its README; runs ab-base, ab-noreason, ab-final.

- 2026-10-18 — The Assistant panel and the graph's energy flows tuned against measurement (owner request, experiment).
  - The panel resizes from a divider (300–720 px, the graph keeps 420 px), folds by drag, answers the keyboard, is
    kept per browser and resets. A drag costs 29 ms frames on the dense graph, against 167 ms for a naive live
    resize: the graph's layout holds, the width variables are not inherited, a long conversation reflows at rest.
  - The chat reads compact: 13 px answers at 1.55, emphasis at 600, tabular figures, quieter meta and chrome. The
    conversation shows 47% more text at 1440×900; a phone keeps 14 px answers and a 16 px input.
  - Static edges are quieter. A spark is a light core of its edge's hue on its own layer, the glow a faint stroke,
    not a filter, and the flicker is gone. Chrome's CPU while flows run: 3.80 → 1.20 cores on Tổng quan; a 30-flow
    graph went from 10 fps to 60 fps.
  - Documents: docs/brd/testing/panel_and_flows_report.md (new) and its screenshots; scripts/perf_flows.py and
    scripts/perf_dock_drag.py (new).

- 2026-10-18 — The assistant stress test done (owner request 2026-10-17, ASSISTANT_STRESS_PLAN T0–T4, experiment).
  - 81 multi-turn conversations as real customers, on the real model and a served copy. Final run: 76 of 81 by the
    machine checks, 80 of 81 by hand; 49 BRD requirements exercised, 46 held.
  - 32 defects; 28 fixed with tests that fail without their fix. The S1 (D13): a customer naming another family's
    id was answered with that family's data, because the tools' nested runs saw no session. Fixed here; `main` has
    the same code (the owner's decision).
  - Most defects shared one cause: a tool told the model a headline and left the rest on the page. Open: D29
    (intermittent guide retrieval), D31, D18 (data), D05 (rounding).
  - Not production-ready until D13 is on the branch that serves customers (readiness.md). US$1.97 of the US$3 cap.
  - Documents: docs/brd/testing/assistant/ (catalogue, results, defects, coverage, readiness, browser, runs),
    traceability OWN-AS-03, OWN-AS-04, BRD-RULE-ROLE-02, the customer guide's graph section, the plan's progress.

- 2026-10-17 — The unified graph and its money flows built (experiment, UNIFIED_FLOWS_PLAN U1–V; OWN-GW-33…50:
  17 implemented_verified, OWN-GW-34 partially implemented because the data has no transfer rows).
  - Money edges carry amount, monthly rate and direction, and their motion follows them. Actual, estimate and
    hypothetical look different.
  - Several scenarios combine on the server with nothing counted twice, and never in net worth.
  - Edges can be picked, with source, formula, assumptions, confidence and downstream. Categories open on Dòng
    tiền. Goals sharing a pool say so once.
  - The assistant knows the lens, the selection and the active scenarios; two read tools, `lien_ket` and
    `so_sanh_kich_ban`.
  - The V audit with scenarios active found 27 crossings; an active scenario now sits on its own spoke. Edge ends
    meet their rims. Another member's holdings are marked in Gia đình.
  - The audit is at 0 on every lens, real and 3×, with and without scenarios. Idle frame time is within the gate.
  - Documents: FEAT-40 “As built” and “Feature map”, matrix OWN-GW-33…50, unified_flows_report.md (new), the
    plan's as-built notes, screenshots SCR-CL-12-flows, -scenarios, -edge, -compare (desktop, phone).

- 2026-10-17 — Owner request recorded: the unified graph and its money flows (OWN-GW-33…50, planned). The audit
  found: goals share one 4,03 tỷ pool, policy impacts have no per-class split, no transfer rows exist, and
  scenarios cannot be combined. Documents: sources SRC-05, owner_requirements.md, FEAT-40 “Money flows,
  scenarios and the assistant”, matrix, docs/UNIFIED_FLOWS_PLAN.md.

- 2026-10-17 — The central wealth core and the graph's layout built (experiment, GRAPH_CORE_LAYOUT_PLAN C0–V,
  OWN-GW-20…32 implemented_verified).
  - One rounded ring with slots sized from the measured labels. Groups fold into “+n” nodes instead of squeezing,
    and a group too big opens partly. Routes are checked against every disc and label.
  - The audit is at 0 everywhere: edges through nodes went 3/9 → 0 on the real graph and 38/66 → 0 on the 3× graph.
  - Tập trung (`f`) and Vừa khung (`0`). Edge emphasis: money first, summaries faint, a pick keeps only its edges.
  - The core: layered glass, a slow breath, ports and band on the sparks' beat, assistant and flow states,
    still under reduced motion, net worth ≥ 7:1. Idle frame cost unchanged.
  - Documents: FEAT-40 “As built”, matrix OWN-GW-20…32, graph_core_layout_report.md (new), the plan's status,
    screenshots SCR-CL-12 replaced plus -core (dark, light), -dense and -group.

- 2026-10-17 — Two owner requests recorded: the central wealth core and the graph's layout and routing
  (OWN-GW-20…32, planned). A stricter audit found spokes through other nodes and labels on every lens (up to 38 on a
  3× graph). Documents: sources SRC-05, owner_requirements.md, FEAT-40 “The centre and the layout”, matrix,
  docs/GRAPH_CORE_LAYOUT_PLAN.md.

- 2026-10-17 — Money in motion on the graph (owner's correction to G9). Studio's spark now runs all the time on
  every real money edge: income into “My Wealth”, spending and this month's loan and card repayments out. Not on
  estimates or scenarios; hidden under reduced motion; idle frame cost measured as none. Documents: FEAT-40, OWN-GW-16
  evidence.

- 2026-10-17 — Assistant sessions (experiment, SESSIONS_PLAN S0–S5, OWN-SS-01…08).
  - Sessions renamed, archived and restored. Titles and goals are written by the model after the answer, never over
    the person's name.
  - A turn is kept from its start, and a reload follows it to its answer.
  - Compaction writes seven fixed sections, kept on the session; `doc_lai_phien` reads past them.
  - The panel has a session bar, “Trò chuyện mới”, and a history with search, tabs and day groups.
  - Documents: FEAT-37, assistant.md §5, matrix OWN-SS-01…08, sessions_report.md, screenshots SCR-CL-10-session
    and -history.

- 2026-10-17 — The graph refined: hierarchy and Studio-style dataflow (experiment, G8–G10, OWN-GW-15…19).
  - Spokes by default, relations on demand, holdings on pick, labels and nodes that never overlap (crossings 104 → 0
    on Tổng quan); the centre's text fits its disc.
  - Silk edges; pulses home from what the assistant read, through the classes a news item moves; failure in red with
    no pulse; hollow for scenarios; a pulse never in a money colour, and the legend says it is a read.
  - Performance on a 3× graph; two profiling fixes (the live bubble, edge restyling). Screenshots SCR-CL-12 replaced
    (same names) and two added. Documents: FEAT-40, matrix OWN-GW-15…19, graph_workspace_report.md, the plan.

- 2026-10-17 — The persistent financial graph, built and verified (experiment, G1–G7).
  - The Customer's app is one page: lenses on a persistent graph (cash flow, reserve and stress scenarios as nodes,
    certainty on every edge), the old pages as sheets at their old addresses, the dock (Trợ lý, Thông tin), the
    strip. `POST /api/assistant/stream` sends each real tool step; the graph lights only on those, and a broken
    stream is said and marked failed. OWN-GW-01…14 implemented_verified (18 tests); one live question US$0.0014.
  - Documents: graph_workspace_report.md (new), matrix OWN-GW, SCR-CL-12 screenshots in assets/current_ui, the
    plan's status. Branch `exp/graph-workspace` only; `main` and the live demo unchanged.

- 2026-10-17 — The persistent financial graph, documented before building (owner request, experiment).
  - The owner's request and concept image registered (SRC-05); OWN-GW-01…14 (planned); FEAT-40 with the capability
    map of every Customer screen to its lens or sheet; SCR-CL-12 (proposed); ADR-0035; the Customer workspace tree in
    information_architecture.md; assistant.md §9b (the streaming door).
  - Built on branch `exp/graph-workspace` and its own public link; `main` and the live demo unchanged. Plan:
    docs/GRAPH_WORKSPACE_PLAN.md.

- 2026-10-17 — The assistant's eval gate and readiness report (ASSISTANT_PLAN A8).
  - 32 cases in 10 kinds on the real model, plus 8 turns at once; a gate in the eval file. Run 1 failed security
    (a claimed role was not refused); after two rules (a claimed role changes nothing; no worked-out figures) and two
    grader fixes, run 2 passed: 31/32, security 4/4, no leaks, p95 6.2 s, US$0.002 a turn.
  - Cost per turn from the provider's own count, tools included (operonx-agents 0.3.1); `cost_usd` in the turn and
    the audit record.
  - Documents: assistant_readiness.md (new), assistant_eval.md A8, assistant.md §9 and §11, ADR-0034, matrix
    OWN-AS-23…25, ASSISTANT_PLAN.

- 2026-10-17 — The Agent Ecosystem Map (ASSISTANT_PLAN A7).
  - The Agent page opens on the map: the person, the assistant and its tools, the data, the CIO desk, the rules and
    the background agents; 27 lines, each the code that makes it; states from the parts' records, matched with the
    traces of the same runs in a test; a part's runs and a run's steps in drawers; a list per group on a phone; the
    panel links to it (CIO, Compliance, Admin). `GET /api/agents/map`, `GET /api/agents/map/<part>`.
  - Privacy: the `assistant`, `copilot` and `assistant_conversations` services no longer write traces (their inputs
    held the question in clear); the map reads turns from the audit log.
  - Documents: assistant.md §7, ADR-0033, FEAT-15, SCR-CIO-08 (screenshots), matrix OWN-AS-20…22, ASSISTANT_PLAN.

- 2026-10-17 — Background agents (ASSISTANT_PLAN A6).
  - The memory consolidator (`assistant_consolidate`, every 5 minutes): an idle conversation that changed becomes
    ≤ 5 long-term items (checked like a person's own, repeats merged, “trợ lý tự rút ra” on the Bộ nhớ page), only
    where the model may read it; ≤ 8,000 tokens; two retries; tokens and cost per run and per day. Real model:
    ~US$0.00024 a conversation.
  - Follow-ups: `theo_doi`, `theo_doi_cua_toi`, `huy_theo_doi` (35 tools): a market series above or below a level,
    or a topic in an approved event; checked by the market and news jobs with no model; fired once, in the bell for
    every role; the Bộ nhớ page lists and cancels them.
  - Fixed before release: the token estimate (3 characters a token assumed, 1.64–1.70 counted).
  - `read()` in `web/core/core.js`: a POST that only reads (the bell's follow-ups, the Bộ nhớ page's lists) no
    longer clears the tab cache (it made every page wait for the server: `tests/ui/test_speed.py`).
  - `.operonx/guide`: the kb pages and operonx 1.30.1 (what `operonx serve` already wrote on the server).
  - Documents: assistant.md §7/§11, ADR-0031, FEAT-39, matrix OWN-AS-12/18/19, assistant_eval.md, ASSISTANT_PLAN.

- 2026-10-17 — Knowledge and the web (ASSISTANT_PLAN A5).
  - `huong_dan`: a Vietnamese user guide per role and page (`docs/huong-dan/`), the “Cách tính” formulas and the
    glossary in an operonx-kb collection; the answer links the page to open. 24/24 product questions find their
    page in the first three, 10/10 formula and term questions.
  - “Tài liệu của bạn” on the Bộ nhớ page and `tai_lieu`: a person's documents (Word, PDF, Excel, PowerPoint, text;
    ≤ 5 MB), read by them and, for a client, their RM; deleted for good; audited without content.
  - `tim_tren_web`: OpenRouter's web search on the scrubbed question, URLs cited, certainty stated, 20 per person and
    500 a day; 9.1 s and US$0.012 a search on the real model.
  - Lexical only: embeddings measured (bge-m3 hybrid one more first place out of 24, a second slower), not used;
    nothing goes to an embedding service. ADR-0029 amended.
  - Fixed: a graph input named `name` broke the served Bộ nhớ service (the serve layer passes `name`), now
    `file_name`; `data/kb/` gitignored.
  - Upstream: operonx-kb 0.2.6 (lexical-only collections), operonx 1.30.1 (`register(persist=False)`).
  - Documents: assistant.md §6/§9, ADR-0029, ADR-0030, FEAT-38, matrix OWN-AS-02/07/16/17, assistant_eval.md,
    ASSISTANT_PLAN.

- 2026-10-17 — Memory and the archive (ASSISTANT_PLAN A4).
  - Long-term items (Sở thích, Mục tiêu, Thông tin 180 days, Giới hạn), kept only when the person asks and confirms,
    never an amount, an account number or someone outside the family; the reading model's instructions carry them.
  - Tools `nho_lai`, `ghi_nho`, `quen`, `tim_lich_su` (29 in the registry); the Bộ nhớ page on every role: correct,
    forget one or all, open or delete a conversation, search the archive (0.5 s for a year of daily conversations).
  - Compliance's `assistant_retention` (two-person, default 365 days) and its daily job; every deletion overwrites
    the file (VACUUM, 0.7 s on 25 MB); a finished run's state no longer outlives its turn.
  - Upstream: operonx-agents 0.3.0 `memory` (store protocol, SQLite store with a sealing codec, tools with verifiers).
  - Documents: assistant.md §5/§9, FEAT-37, matrix OWN-AS-12…16, ASSISTANT_PLAN.

- 2026-10-17 — Conversations on the server (ASSISTANT_PLAN A3).
  - Every assistant turn belongs to a conversation in `assistant.db`; the panel resumes the latest on any device,
    lists, opens and deletes them (`POST /api/assistant/conversations`); owner-only, deletion audited without text.
  - The model's side is an operonx-agents session per mode (the barrier closing mid-conversation sends nothing read
    before), compacted past 75 % of a 24k-token budget into a summary, every turn kept; the panel says when.
  - Sealed with the data keys; key rotation covers `assistant.db`. The tab's `sessionStorage` copy is dropped.
  - Upstream: operonx-agents 0.2.4 (one SQLite connection per file, reads without a write lock; 50 sessions: lock
    errors before, none now) and 0.2.5 (compaction across runs: a conversation of plain answers never compacted).
  - Documents: assistant.md §5/§9/§10, FEAT-37, matrix OWN-AS-10/11.

- 2026-10-17 — The assistant (ASSISTANT_PLAN A2): the Copilot panel now asks `POST /api/assistant`.
  - An operonx-agents run over the role's tools, several steps a turn.
  - Writes wait with their plan for the person who asked, then run once and are read back.
  - Answers cite their pages, sources and date, and say how they were written (model / template behind the barrier /
    keyword fallback when no model answers).
  - Real-model eval subset 10/10 twice (p50 ≈ 5.4 s). Its first run found the model asking for a confirmation in
    prose instead of calling the write; fixed.
  - Documents: assistant.md §3, FEAT-32, testing/assistant_eval.md, matrix OWN-AS-01/05/06/08/09.

- 2026-10-17 — The assistant's tool registry (ASSISTANT_PLAN A1): the Copilot's 13 tools moved into
  `src/assistant/` and 12 more wrapped from served graphs (reads: forces on wealth, search, the review queue, events,
  system alerts, contacts; writes: send a scenario option, log a contact, recommend, specialist decision, flag an
  event urgent, acknowledge an alert), each with roles, a timeout and, for writes, a plan and a verifier that reads
  the state back; operonx-agents 0.2.3 (`@tool(verify=)`, upstream) — assistant.md §4/§9, FEAT-32, matrix
  OWN-AS-03…06.

- 2026-10-16 — The assistant's architecture (ASSISTANT_PLAN A0): audit of the Copilot, agents, storage and OperonX;
  the owner's brief registered (SRC-05) and split into OWN-AS-01…25; the target architecture with the storage
  measured (`scripts/bench_chat_store.py`: chat in its own SQLite WAL file, ~127 turns/s against ~10 at the BRD's busy
  hour; inside `state.db`, lock errors and multi-second tails) and web search proven on the existing OpenRouter key;
  nine decisions — assistant.md, ADR-0026…ADR-0034 (ADR-0012 amended), FEAT-37…39, FEAT-15/32 next steps, matrix §5.

- 2026-10-16 — Pages switch at once: a page's reads are kept in the tab's memory, so going back to a page draws it
  from what it had (6–45 ms, was 20–480 ms) while the same reads go to the server again and the page is drawn once
  more if an answer changed; any change made in the tab forgets them; every page module of the role is imported
  while the browser is idle. The page reads (dashboard, overview, flows, feed, goals, alerts, scenario, search) are
  no longer traced — a trace took two thirds of their time (feed 226 → 71 ms). The Cá nhân / Gia đình switch shows
  only where the family has someone else, with a “?” saying whose assets each view counts and who has not consented
  — ADR-0024 (memory only, not `no-store`'s HTTP caches).

- 2026-10-16 — Availability measured (BRD_REMAINING_PLAN G5, NFR-03): a heartbeat every 20 seconds inside the
  server; availability = business minutes (Mon–Fri 08:00–17:30, Vietnam time) with a beat ÷ business minutes, from
  the first beat; Hệ thống shows the month so far, the monthly report each month with its outages and “Cách tính”;
  an Admin alert below 99.5 %; job run records bounded (operonx 1.30.0 `keep_runs`) — matrix (NFR-03 verified),
  BRD_COMPLETION_REPORT.md.

- 2026-10-16 — The move to the bank (BRD_REMAINING_PLAN G4, RULE-DATA-10): `scripts/export_postgres.py` maps every
  table to PostgreSQL, the fields queries read made columns and the JSON lists and maps made 15 child tables, client
  values still sealed, loaded into a real PostgreSQL 16 and checked row for row (counts, sums, every row rebuilt);
  the audit log copied hourly to write-once segments, chained and checked against the database, so a history
  rewritten with its chain recomputed is caught; `/healthz` and the System page show them; the migration guide —
  ADR-0025, bank_migration.md, matrix (RULE-DATA-10 verified), BRD_COMPLETION_REPORT.md.

- 2026-10-16 — Encryption, secrets and the attack suite (BRD_REMAINING_PLAN G3, NFR-07): client data sealed at rest
  per column with AES-256-GCM (row-bound, rotating keys, `scripts/rotate_keys.py`), chosen by scanning a populated
  database; keys from a Vault-compatible store, a secrets folder or the environment; security headers (CSP by hash,
  no framing, nosniff, HSTS over TLS, no-store on the API) and cross-site writes refused on every response (operonx
  1.29.0 middleware); an attack suite (at rest, rotation, secrets, headers, CSRF, forged sessions, another family,
  SQL, paths, upload size, stored markup); request checks answer 400, not 500 — ADR-0024, matrix (NFR-07 verified),
  non_functional_requirements, BRD_COMPLETION_REPORT.md.

- 2026-10-16 — The client-data barrier (BRD_REMAINING_PLAN G2, NFR-08): a `client_ai` setting (Admin, two people):
  `demo` (today's, the public demo), `onprem` (the statement reader and the declaring chat on `llm:onprem`, whose host
  must be on `onprem_hosts`), `off` (their rules); one guard on every `llm:` call (operonx 1.28.0
  `ResourceHub.guard`) refuses, in onprem and off, a call bound outside the bank carrying any client's id, name,
  dependent or account number, before anything is sent, and audits it; `/healthz` reports the setting; a test with a
  recording OpenAI-compatible server proves it at the wire — ADR-0023, FEAT-22, FEAT-23, matrix (NFR-08 verified),
  non_functional_requirements, BRD_COMPLETION_REPORT.md.

- 2026-10-16 — “Cách tính” on every number (BRD_REMAINING_PLAN G1, NFR-11): one server catalogue of about 95
  formulas (`src/explain/`, `GET /api/how`), each naming the function that computes it; every money or percent
  figure of every page and role opens the drawer with its formula and inputs (and the code, for staff); settings,
  parameters and demo sample data say what they are; a browser test walks every route, the states a click reveals
  and the detail pages, and fails on any figure without a formula — FEAT-09, matrix (NFR-11 verified), Q-14
  resolved, design_system, non_functional_requirements, BRD_COMPLETION_REPORT.md.

- 2026-10-16 — The remaining rules and the scale test (BRD completion F10): each goal's VND impact at every
  horizon and band, its share of the goals' pool run through the same engine (BR-08; the overview card of policy
  and project items relabelled as their own rules, Q-03); the client's own “Cách tính” per effective event (F-D9);
  15- and 5-minute limits on the CIO agent and the challenger, enforced on each model call (WF-03, WF-04); the
  served schedules asserted (FR-101, WF-01); browser tests for the goal branch's placements and the “Nội bộ”
  stamp (FR-603, SEC-03); 6,500 families applied in 167 s and every family read ≤ 0.3 s with them all stored
  (NFR-01; a family read decodes its own row, the consolidation reads each client once per run, stores create
  their tables once) — FEAT-01, 04, 05, 08, 09, 10, 13, matrix (BR-08, FR-101, FR-603, NFR-01, WF-01/03/04,
  SEC-03 verified), api_reference, client.md, BRD_COMPLETION_REPORT.md.

- 2026-10-16 — The policy agent and the policy radar (BRD completion F9): Compliance adds a policy document from
  the Official Gazette (the server reads the gazette's signed PDF, extracts the text, keeps its hash) or an
  official page; a second Compliance person verifies the source; the policy agent (live on `llm:cio` with the new
  `policy` prompt, or mock) summarises only verified text, every quote checked word for word inside the article it
  names, a failing answer sent back at most twice; it sees one document and no client data; the radar (our
  reading of Q-09, labelled “Đề xuất”) keeps each document's status path and marks what changed since the last
  look — FEAT-16, catalogue (FEAT-15), matrix (FR-306, AI-01 verified), api_reference, compliance.md (SCR-CMP-05).

- 2026-10-16 — The newsletter and conflict of interest (BRD completion F8): the CIO drafts a general letter from
  1–6 approved views (impacts in words, tickers counted not named, scenarios, outlets), the opening by template or
  the CIO agent under a content guard (forbidden wording, tickers, restricted names, the CONTENT-02 labels) with the
  template as fallback; same time for Private and retail unless a reason is recorded; Compliance approves or
  returns, never the author; a preview, never sent; conflict of interest is a structured field on research and
  letters, a related party (Compliance's `related_parties`) cannot go undeclared, and the client reads the
  disclosure on the impact page — FEAT-17, FEAT-03, FEAT-13, matrix (FR-801, CONTENT-01/02/03, SEC-04 verified),
  api_reference, cio.md (SCR-CIO-14), compliance.md (SCR-CMP-04).

- 2026-10-16 — Alerts and the central log (BRD completion F7): one alert per failing thing (a news feed, a market
  series, an agent run, the audit chain checked hourly by the new `audit_check` job, a rejected inbox package, the
  zone sync), counted while it keeps failing and resolved when it works again; staff see their kinds in the bell
  with “Đã xem” (audited), Admin all of them in Hệ thống with the central JSON-lines log; a provider that cannot be
  reached fails the run with why instead of leaving it running, and an outage test shows computing, runs and reads
  unaffected — FEAT-36, FEAT-34, matrix (NFR-12 verified; NFR-03's AI part verified), api_reference, admin.md.

- 2026-10-16 — Background runs, the AI zone and inbox mode (BRD completion F6): “Chạy Agent CIO” queues a job
  that the `agent_worker` job runs, and the event page follows it; Admin chooses live, inbox or mock (`ai_mode`);
  the AI zone is a second process (`app/zone.py`) with its own database and a catalogue-only data folder, fed the
  approved catalogues and released research by the signed `zone_sync` job; it fetches the feeds itself, runs the
  agent under a daily cap and pushes signed packages to the write-only `POST /api/inbox`; the `inbox_import` job
  takes each through a live run's checks (news matched to the bank's own fetch) or rejects it with the error;
  Hệ thống shows the inbox and the syncs; `operonx run <job>` no longer refused as a signed-out request —
  ADR-0022 (ADR-0009 superseded in part), FEAT-19, FEAT-04, matrix (FR-307, AI-13, ZONE-01/02/03/06, LC-04,
  SEC-07 verified), api_reference, admin.md (SCR-ADM-01).

- 2026-10-16 — Identity and access complete (BRD completion F5): every served route walked as seven people
  against a written matrix (reads by role per path, actions by person, role and family); refused actions answer
  403 with the reason and signed-out 401 (operonx 1.27 `http_status`); holes the walk found closed (declaring
  assets, uploading a statement and proposing a plan for another family; an RM deciding another family's review
  item; anyone fetching the news); the RM-to-family assignment is configuration (Admin); Hệ thống for Admin (jobs,
  feeds, agents, audit chain, history load on request through the `market_load` job, accounts) — FEAT-12,
  FEAT-14, matrix (SEC-02, ROLE-04 verified), api_reference, admin.md (SCR-ADM-01), screen inventory.

- 2026-10-16 — Configuration completes (BRD completion F4): return assumptions (CIO), forbidden phrases and
  consent (Compliance), prompts and models (Admin, two people) as versioned configuration the product reads; the
  fixed eval set (six sample events, `agent_eval` job) gates every prompt or model change; each agent node records
  the prompts version; asset classes and analyst groups declared by configuration (NFR-06); a second Admin
  account — FEAT-14, FEAT-04, agent_workflows, matrix (FR-701, NFR-06, AI-02, SEC-05, MEAS-07 verified; SEC-04
  partial), SCR-CIO-09.

- 2026-10-16 — Accuracy over time and the measurement reports (BRD completion F3): the model walked forward over
  2021–2026 market history per factor and horizon (band coverage, direction from engine step 2); every approved
  view's forecasts recorded at approval and scored by the daily `accuracy_score` job; monthly misses, approval
  speed and edits, news-to-RM time, inbox and agent timing; AI-05 scoped to agent answers (a CIO edit gets the
  challenger's R2) — FEAT-18, FEAT-04, matrix (BR-15, KPI-03/04, MEAS-01/02/03/05, WF-09, NFR-02 verified; KPI-01
  partial), screen_inventory, cio.md (SCR-CIO-12, SCR-CIO-13), api_reference.

- 2026-10-16 — Model estimated from market history (BRD completion F2): volatilities and correlations of 12/15
  factors from 55 months with 20 % shrinkage, proposed by a CIO and approved by a second; out-of-sample check
  2/2024–8/2026 (85 % inside P10–P90) written up for Model Risk; AI-05 enforced on every answer — FEAT-07,
  matrix (ENG-11, MEAS-08, AI-05 verified), model_validation.md, SCR-CIO-07.

- 2026-10-16 — Market data layer (BRD completion F1, second half): seven scheduled jobs fetch public sources
  (VNDirect/Vietcap, cafef, HNX/worldgovernmentbonds, Vietcombank/MSN, MSN, Binance, PNJ) into SQLite with
  fallbacks and a record of every fetch; `market_backfill` from 2020; the 15 factors' monthly moves with their
  provenance; `price_sources` and `ticker_map` configuration (Admin); “Dữ liệu thị trường” for CIO and Admin —
  FEAT-35, ADR-0021, matrix (BR-15, KPI-03/04, MEAS-01/02 unblocked → planned; ENG-11 note), integrations,
  api_reference, SCR-CIO-11.

- 2026-10-16 — Sign-in and the people table (BRD completion F1, first half): every person (customers, household
  members, dependents, RMs, CIOs, Compliance, Admin, specialists) is a row in SQLite; everyone who acts signs in
  with their own account (scrypt password, signed HttpOnly session) and sees only their role's pages and the
  families they may see; three RMs with assigned families; the role switcher is gone; demo accounts listed with
  `MF_DEMO_ACCOUNTS=on` — FEAT-12, ADR-0020 (supersedes ADR-0006), matrix (SEC-01, ROLE-02 verified; SEC-02,
  ROLE-04 partial), Q-17 resolved, api_reference, screen inventory.

- 2026-10-16 — UI redesign R7: regression — every route of every role on desktop and phone, light and dark, in the
  suite (254 tests); Living Interface re-measured (rest unchanged, one question 170 ms, JS 62 KB from 135 KB); an
  approved view's checklist no longer shows “Đang chờ duyệt” as failed; final report `docs/UI_REDESIGN_REPORT.md`
  — FEAT-33, PRODUCT_OVERVIEW, UI_REDESIGN_PLAN §4.

- 2026-10-16 — UI redesign R6: the public demo runs the real models (CIO agent, challenger on another vendor, Copilot
  router); `scripts/demo_walkthrough.py` fills a demo over HTTP from fetched news — events, agent, challenger,
  answers to critical findings and approvals, each reason naming the script; the live demo now has two runs in
  effect and one view waiting for the CIO — FEAT-04, matrix (OWN-UI-06), integrations, `.env.example`,
  UI_REDESIGN_PLAN §4.

- 2026-10-16 — UI redesign R5, Copilot 2.0: answers carry the data's date, the answer time and their sources, and a
  card drawn from the tool's numbers (figures, list with chips and progress, bars, chain); new tools `dieu_tra` (an
  approved event's path from the impact graph) and `kich_ban` (a stress test through `scenario_flow`, chosen by
  words); every call is an audit row with the scrubbed question; suggestion chips; the goals followed in the browser
  — FEAT-32, matrix (OWN-UI-05 verified, KIT-COPILOT-02), api_reference, client.md SCR-CL-10, 3 screenshots,
  UI_REDESIGN_PLAN §4.

- 2026-10-16 — UI redesign R4: Bản đồ tài chính, the overview graph of the board (client in the centre; asset
  classes opening onto holdings, data sources, followed goals, flagged risks, policy items, approved news events;
  every edge names its record; node → page; `POST /api/overview`); the News Impact panel on Đồ thị tác động
  (direction, chain, each event's own share per asset); the event timeline on Tin tác động; the CIO's whole-run graph
  (`GET /api/runs/{id}/graph`) — FEAT-30, matrix (OWN-UI-04 verified), client.md SCR-CL-05/09/11, cio.md SCR-CIO-10,
  inventory, IA, api_reference, assets (9 screenshots), UI_REDESIGN_PLAN §4.

- 2026-10-16 — UI redesign R3: the eight pre-redesign pages rebuilt in the board's look as module pages (Chi tiết,
  Tài sản, Kế hoạch, Khẩu vị rủi ro, Chi phí chính sách, Chuyên gia / Duyệt đề xuất, Hiệu quả tư vấn one client and
  all), every block and action kept; `web/app.js`, `app.css`, `charts.js`, `fmt.js` deleted; the shell owns the client
  picker, scope and “Làm lại demo”; each route renders into its own element (a late redraw of an earlier page no
  longer breaks the page shown); the UI's files are served `no-cache`; icon markup fixed (text after an icon was
  swallowed) — ADR-0019 (supersedes ADR-0013), ADR-0003 note, matrix (OWN-UI-01, 02 verified), owner_requirements,
  client.md, rm.md, screen_inventory, information_architecture, assets (16 screenshots), UI_REDESIGN_PLAN §4.

- 2026-10-16 — UI redesign R2: Toàn cảnh as on the concept board (four Pulse cards with small charts, Sankey with a
  colour and icon per category, ratios and flow dots, donut, impact cards, goals card) — FEAT-29, FEAT-33 note,
  matrix (KIT-UX-01, 03 verified; OWN-UI-01), client.md SCR-CL-08, design_system, 4 screenshots, UI_REDESIGN_PLAN §4.

- 2026-10-16 — UI redesign R1: board look (tokens, header with tagline, search, bell, demo roles on the tabs row),
  Lucide icons, icon chips, pills, small charts, one look for controls, round Copilot button; `POST /api/search`;
  owner request recorded as OWN-UI-01…07 — FEAT-34, owner_requirements, matrix §5, sources, design_system,
  interaction_patterns, api_reference, UI_REDESIGN_PLAN §4.

- 2026-10-16 — UI redesign R0: browser tests in the suite (`tests/ui`, Playwright, `ui` marker; `.[ui]` extra); the
  shell signals `mf:page` after a failed render too — matrix (KIT-COPILOT-01, OWN-MOTION-02/04 verified, KIT-UX-07),
  regression_coverage, docs/UI_REDESIGN_PLAN.md §4.

- 2026-10-16 — Owner decisions D-01…D-03: BRD quotes stay public, the mock demo keeps AI on (ADR-0018); FR-404 rule
  kept and decided (ADR-0017, Q-11 resolved; the impact page no longer says “chờ CIO xác nhận”) — decisions,
  open_questions, functional_requirements, matrix (FR-404, NFR-08), FEAT-08, PRODUCT_OVERVIEW, docs/TO_DISCUSS.md.

- 2026-10-16 — Living Interface (owner request B-01): Copilot states, evidence marks (`focus` on answers, `key` on
  feed items), motion rules and tokens; new requirement source OWN-* (SRC-05) — FEAT-33, FEAT-32, owner_requirements,
  matrix (§5, KIT-UX-06), checker, sources, README, design_system, interaction_patterns, client.md, inventory,
  api_reference, regression_coverage, PRODUCT_OVERVIEW, 6 screenshots.

- 2026-10-16 — Versioned configuration with owners and approval (FR-701; SCR-CIO-09; ADR-0016 resolves Q-15) —
  FEAT-14, matrix (BR-07, FR-701, RULE-SEC-04/05), business_rules, open_questions, cio.md, inventory, IA,
  api_reference, decisions, 2 screenshots.

- 2026-10-16 — Agent catalogue and AI quality (FR-703, RULE-MEAS-04; SCR-CIO-08) — FEAT-15, matrix, cio.md,
  inventory, IA, api_reference, agent_workflows, 2 screenshots.

- 2026-10-16 — Copilot live router run recorded; D-03 updated (the live demo has AI on) — FEAT-32,
  REDESIGN_KIT_PLAN, docs/TO_DISCUSS.md.

- 2026-10-16 — BRD gaps: audit export (FR-702), `/healthz` protections (RULE-SEC-10), daily token budget and
  tokens per event (NFR-10), “Nội bộ” on staff views (RULE-SEC-03), regulation notes on the planning tab (FR-603,
  Q-20), client sources by outlet (RULE-CONTENT-02); D-03 raised in docs/TO_DISCUSS.md — matrix, FEAT-04, FEAT-11,
  open_questions, api_reference, compliance.md.

- 2026-10-16 — Kit K6: regression sweep and status — regression_coverage, PRODUCT_OVERVIEW, matrix header,
  REDESIGN_KIT_PLAN §5.

- 2026-10-16 — Kit K5 built: OneWealth Copilot (SCR-CL-10; `POST /api/copilot`; scrubber, keyword and `llm:copilot`
  routers, 11 tools, confirm for writes) — FEAT-32, ADR-0012 status, matrix (KIT-COPILOT-01…05), client.md,
  inventory, IA, api_reference, 3 screenshots.

- 2026-10-16 — Kit K4 built: Intelligence Feed (“Điều đáng chú ý” on SCR-CL-08; `POST /api/feed`) — FEAT-31,
  matrix (KIT-UX-05), client.md, inventory, IA, api_reference, SCR-CL-08 screenshots retaken.

- 2026-10-16 — Kit K3 built: Đồ thị tác động (SCR-CL-09; `GET /api/families/{id}/graph`) — FEAT-30, matrix
  (KIT-UX-04), client.md, inventory, IA, api_reference, 4 screenshots.

- 2026-10-16 — Kit K2 built: Toàn cảnh (SCR-CL-08: Pulse, Wealth Map, Money Flow; `POST /api/flows`); the former
  overview is “Chi tiết”, unchanged — FEAT-29, FEAT-21, matrix (KIT-UX-01…03), client.md, rm.md, inventory, IA,
  api_reference, 3 screenshots.

- 2026-10-15 — Fixed DEF-01 (`.check` scoped to new pages), DEF-04 (`AUDIT_HMAC_KEY` in `.env.example`), DEF-05
  (advisory dates; page labelled illustrative, Q-19 resolved) — regression_coverage, client.md, rm.md, inventory,
  FEAT-25, FEAT-28, open_questions, SCR-CL-06 screenshot.

- 2026-10-15 — Fixed DEF-02 (RM decides on new SCR-RM-06, role-checked; client queue read-only) and DEF-03 (news
  dismiss/release role-checked); built FR-404 goal impact per run on our definition (Q-11) — matrix (BR-04, BR-08,
  FR-103, FR-105, FR-404, RULE-ROLE-03, RULE-SEC-02, BRIEF-SCEN-03, BRIEF-FLOW-02), FEAT-02, 08, 12, 27, screens
  (client, rm, compliance, inventory, IA, journeys), api_reference, domain_model, regression_coverage,
  acceptance_criteria, open_questions, 4 screenshots.

- 2026-10-15 — Repository created: 61 BRD requirements, 7 KPIs and 97 rules extracted; 29 brief and 19 kit
  requirements; 32 features; 21 screens + 4 proposed with 30 screenshots; 15 ADRs; 23 open questions; 5 defects
  found (DEF-01…05); FR-404 found not built (news plan corrected); checker and `tests/test_brd_docs.py` added —
  everything under `docs/brd/`, `scripts/check_brd_docs.py`.

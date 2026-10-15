# Changelog

Newest first. One line per meaningful change: date — what — documents touched.

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

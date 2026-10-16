# Changelog

Newest first. One line per meaningful change: date — what — documents touched.

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

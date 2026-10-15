# Changelog

Newest first. One line per meaningful change: date — what — documents touched.

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

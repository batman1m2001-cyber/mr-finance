# Changelog

Newest first. One line per meaningful change: date — what — documents touched.

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

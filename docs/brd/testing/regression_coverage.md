# Regression coverage, latest results and known defects

## How to run

```bash
uv run pytest                         # the whole suite (offline; fake models, written feeds)
uv run pytest tests/test_brd_docs.py  # this documentation repository's checks only
uv run python scripts/check_brd_docs.py [--brd <path to the BRD .docx>]
uv run operonx run statement_reading  # the statement-reading eval (needs MF_AI=on and a model for 5/5)
```

## Latest recorded run

| Date | Commit | Command | Result |
|---|---|---|---|
| 2026-10-16 | kit K2–K5 (PR #19–#22) | `uv run pytest -q` | **195 passed** in 65 s (+ `test_flows.py` 4, `test_graph.py` 3, `test_feed.py` 5, `test_copilot.py` 7, DEF-05 1); checker 0 errors |
| 2026-10-15 | fix DEF-02, DEF-03, FR-404 | `uv run pytest -q` | **175 passed** in 55 s (+2 FR-404 tests; news, review and verify tests extended); checker 0 errors |
| 2026-10-15 | docs/brd + checker | `uv run pytest -q` | **173 passed** in 53 s (170 + 3 in `tests/test_brd_docs.py`); checker 0 errors, also with `--brd` (61 codes, hash ok) |
| 2026-10-15 | b5e1cb1 (main, before this repository) | `uv run pytest -q` | **170 passed** in 53 s |

Each change to the suite adds a row here (newest first) with what was run and the result, as reported by the tool.
A failing run is recorded too.

## The suite, by area

| File | Tests (functions / cases) | Covers | Features |
|---|---|---|---|
| `tests/test_engine.py` | 20 / 29 | factor-model checks, propagation, three-part bands, mixture, contributions, determinism, loans, bonds, FPT's USD revenue, BRD gold example | FEAT-07 |
| `tests/test_news.py` | 10 / 17 | feed parsing, gates, classification, duplicates, restricted hold, run counts, inbox filters, dismiss, inbox endpoint | FEAT-01, 02 |
| `tests/test_views.py` | 14 / 22 | events and holds, mock agent and node trace, schema, retries → AGENT_ERROR, injection, live-mode safeguards with a fake model, barrier, challenger re-run, edits → re-challenge, critical findings block, approve once, return/withdraw/supersede, CIO-only, reads | FEAT-02, 04, 05, 06, 12 |
| `tests/test_apply.py` | 13 / 13 | approval → run, idempotency, recompute to the dong and tamper detection, supersede, held runs hidden from RMs, withdrawal, RM today, client read, trace, audit chain, triggers, HMAC no-downgrade, endpoints | FEAT-08, 09, 11, 13 |
| `tests/test_research.py` | 9 / 15 | release gate, separation of duties, release time, restricted list, AML wording, name inference (7 cases), BRD §10 example, levels, country limits, reads | FEAT-03, 10 |
| `tests/test_web.py` | 2 / 2 | every routed page module exists and is served; legacy sections kept | UI shell |
| `tests/test_consolidate.py` | 5 | tiers, household and consent, merge | FEAT-20 |
| `tests/test_dashboard.py` | 12 | every section, family sum, services over HTTP | FEAT-21 |
| `tests/test_statements.py` | 7 / 9 | rules, model, fallbacks | FEAT-22 |
| `tests/test_declare.py` | 7 | rules, agent tools, duplicate call | FEAT-23 |
| `tests/test_risk.py` | 8 | path length, adaptivity, profile, drawdown limit | FEAT-24 |
| `tests/test_impact.py` | 10 | formula, severity, sweep job and schedule | FEAT-25 |
| `tests/test_scenarios.py` | 10 | every scenario, parameters, goals, the RM queue | FEAT-26, 27 |
| `tests/test_wealth.py` | 6 | valuation, store, money format, consent | FEAT-20 |
| `tests/test_app.py` | 4 | upload + chat → dashboard; advisory; house views | FEAT-21, 25, 28 |
| `tests/test_demo.py` | 1 | the brief's five-minute demo over HTTP | J6 |
| `tests/test_brd_docs.py` | (added with this repository) | links, IDs, coverage, cited tests, kit hashes | docs |

## UI checks

Not automated beyond `tests/test_web.py`. Recorded manual/scripted checks:

| Date | What | Result |
|---|---|---|
| 2026-10-15 | 21 routes × {1440 × 900, 390 × 844} (desktop all, phone 6, dark 2) captured for this repository with Playwright against the dev server; page errors, console errors and horizontal scroll recorded per capture | 30 captures, 0 page/console errors, 0 horizontal scroll |
| 2026-10-16 | K6 sweep: every menu route of every role (29) × {1440 × 900, 390 × 844} × {light, dark}, plus 3 CIO detail routes × the same 4, scripted with Playwright on the dev server (three effective runs) | 128 page loads: 0 page or console errors, 0 horizontal scroll, 0 error panels |
| 2026-10-16 | K2–K5 click-throughs: Wealth Map drill-down, month switch, Sankey band → rows; feed link → evidence page; graph node → path and detail; Copilot ask, refusal, RM confirm → record approved, navigate | all as expected, no console error |
| 2026-10-15 | U1–U2 acceptance (news plan §9): 21 routes × desktop/phone × light/dark | 84 screenshots, no horizontal scroll, no console error; 6 click-through flows, 5 passed, 1 skipped (a legacy link not shown for the test client) |

## Known defects — `DEF-nn`

| ID | Found | Where | Defect | Requirement affected | Proposed fix | State |
|---|---|---|---|---|---|---|
| DEF-01 | 2026-10-15 | SCR-CL-06 (`web/app.js`, tab `alerts`) | At 1440 px the “Wealth check” card's first column is squeezed: one word per line, a narrow button | usability (BRD-NFR-11) | give the column a minimum width | fixed 2026-10-15 (root cause: `.check` in `web/core/tokens.css` matched the legacy card; scoped to `#page-new`) |
| DEF-02 | 2026-10-15 | SCR-CL-07; `src/review` | The RM approval queue is reachable only from the client's “Chuyên gia” menu (the redesign's shell mapped the legacy “RM duyệt” tab to the client only); `review_flow` checks no role, so whoever opens the page can approve | BRIEF-FLOW-02 | add “Duyệt đề xuất” to the RM's “Khách hàng” section; require role `rm` in `review_flow` | fixed 2026-10-15 (role `rm` in `read_decision`; RM menu “Duyệt đề xuất”; client read-only) |
| DEF-03 | 2026-10-15 | `src/news/ops.py` (`release`, `dismiss`) | Releasing a restricted-list hold and dismissing news check no role: any user id can release a held item | BRD-BR-04, BRD-FR-105, BRD-RULE-ROLE-03 | `roles.require(by, "compliance")` in `release`, `roles.require(by, "cio")` in `dismiss`, and a test for each | fixed 2026-10-15 (`roles.require` in both; tests in `test_news.py`) |
| DEF-04 | 2026-10-15 | `.env.example` | `AUDIT_HMAC_KEY` is read by the code but not listed | AGENTS.md rule; BRD-RULE-SEC-08 | add the name | fixed 2026-10-15 |
| DEF-05 | 2026-10-15 | `data/advisory.json` | Advisory log entries dated after the data date (e.g. 2026-10-24 vs as-of 2026-10-09) | — (Q-19) | regenerate with past dates; label as illustrative | fixed 2026-10-15 (clamped in `scripts/make_advisory.py`; test in `test_app.py`) |

## Coverage gaps (behaviour with no automated test)

- The stressed-branch prompt rule (VN-Index and real-estate credit in core shocks, BRD-RULE-AI-05).
- Page-level click paths (J1–J6) — only HTTP paths are tested.
- Family totals summed in the browser on SCR-RM-01 (system overview §4).
- Feed timing (≤ 10 minutes) and agent duration (≤ 15 minutes) are measured once, not asserted.
- Scale (BRD-NFR-01): 7 people, not 6,500 families.

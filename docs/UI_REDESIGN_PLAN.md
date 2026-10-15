# OneWealth — UI redesign to the kit: audit and plan

The owner asked (2026-10-16) why the interface was never redesigned to the kit, and to recheck everything that was
missed. This document is that recheck and the plan that closes it. Sources re-read in full: the six kit files
(`docs/brd/sources/redesign_kit_2026-10-15/`), the concept board and current-UI reference
(`docs/brd/assets/proposed_ui/`), `docs/REDESIGN_KIT_PLAN.md`, the traceability matrix, `docs/BACKLOG.md`, the
live `.env` (key names only) and the data the visuals would need.

## 1. What was missed or bent

| # | Kit / owner ask | What was done | Gap |
|---|---|---|---|
| G1 | PROMPT_MASTER §2: redesign the UI; the current dashboard is too card-oriented, static and fragmented; less text, more visual | `REDESIGN_KIT_PLAN` D7 (my call, not the owner's) kept the old look; only the new pages got a KPI strip and the Copilot button | The 8 pages that predate the BRD are unchanged: **Chi tiết** is still exactly the screen the kit labels “current UI to improve” (KIT-02); Tài sản, Kế hoạch, Khẩu vị rủi ro, Chi phí chính sách, Chuyên gia/Duyệt đề xuất, Hiệu quả tư vấn (×2) likewise |
| G2 | Concept board (visual direction) | — | No KPI cards with small charts, no donut allocation, no coloured Sankey with category icons and ratios, no news/impact cards with impact chips, no goal progress card, no icons, no header search or notifications |
| G3 | Graph prompt: entities incl. institutions/data sources, risk exposures, alerts, companies/industries; select, filter, **expand**, inspect; cross-feature navigation | Column graph news → event → scenario → factor → asset → family → goal; select, filter, list view | No data-source, risk or alert nodes; no expand/collapse; no overview (the board's radial “Bạn” view); a node does not open its page; no CIO whole-run graph |
| G4 | Motion rules: moving dashes along cash-flow edges; smooth expand/collapse and view transitions | Living Interface (FEAT-33): states, evidence marks, graph path fade | Sankey flow motion and view transitions not built |
| G5 | “Timeline for events and changes” | — | Not built |
| G6 | Copilot: answers with timestamps and source references, structured results and small visuals, Investigate and Analyze through real capabilities, observability | Text answers from templates, an evidence-page link, 11 tools | No as-of time on answers; no structured cards; no investigate (graph path) or analyze (stress scenario) tool; Copilot calls are not in the audit log; the live demo routes by keywords (no `LLM_MODEL_COPILOT`) |
| G7 | §6: refactor the codebase, separate presentation from logic | New pages as modules | `web/app.js` (1,364 lines), `app.css`, `charts.js`, `fmt.js` still render the 8 old pages (ADR-0013 wrapped them) |
| G8 | Owner, 2026-10-16: “go straight to model” (D-03) | Decision recorded | Live `.env` has one model: the CIO agent and challenger (two different models, ADR-0010) still run as the labelled mock; no events or runs on the live demo, so its impact, graph, feed and Copilot impact answers are empty |
| G9 | Kit acceptance: behaviour verified, not just visible | Screenshots and driven browser runs | No browser test in the suite: 14 KIT/OWN/BRD rows are `implemented_unverified` for that reason alone |

Not gaps (data limits, stated on the page instead of faked):
- **No net-worth history**: prices carry “now”, “last month” and (some) “year start”; there is no series. The board's
  net-worth trend line is not drawn. Instead: the month's change split by asset class (real).
- **Investment flows are not in the transactions**, so the Sankey has no “Đầu tư” band (REDESIGN D4).
- Board figures (43,5 tỷ, 180,2 tr, 68 %, “90/84 yêu cầu”) are illustrative and never copied.

## 2. Decisions

| # | Decision | Why |
|---|---|---|
| R-D1 | **The concept board is the target look**, light theme first, dark kept: white cards, soft shadow, 16 px radius, sentence-case section titles, small icon chips per category, one accent (indigo), status colours unchanged | Owner, 2026-10-16; supersedes REDESIGN D7 |
| R-D2 | Every old page is rebuilt as a module page under `web/pages/` on the shared components; a written checklist of every block and action of the old page is ticked before the old code is removed; `web/app.js` and friends are deleted at the end (new ADR supersedes ADR-0013) | G1, G7; kit rule “no silent drops” |
| R-D3 | Small charts only from real fields: income/spending bars from the 12-month cash-flow history, liquidity ring, risk gauge, savings rate, allocation donut, month change by class, goal funding bars | G2; no invented history |
| R-D4 | Icons: an inline SVG subset of Lucide (ISC licence, attributed), no runtime dependency | G2; no build step |
| R-D5 | Header search covers pages, holdings, goals, events and (staff) news over existing reads; the bell lists the feed's items | G2; real data only |
| R-D6 | Graph overview: the family in the centre, rings of asset classes, goals, risks, data sources and events; the column path view stays for “how did this news reach me”; nodes open their page | G3 |
| R-D7 | Live demo: CIO agent `anthropic/claude-sonnet-5.5`, challenger `google/gemini-3.8-flash` (different vendor, as ADR-0010 wants), Copilot router `anthropic/claude-haiku-5.5`; the daily token budget stays; a walkthrough script fills the demo through the real served flows from news the server fetched | G8; owner D-03 |
| R-D8 | Browser tests join the suite (`tests/ui/`, Playwright, the cached Chromium; skipped with a reason when no browser) | G9 |

## 3. Phases (one branch and PR per phase; each ends with tests, desktop + phone screenshots in light and dark, docs/brd updated)

| Phase | Scope | Done when |
|---|---|---|
| **R0 harness** | `tests/ui/`: server on a free port with a temp state; every route of every role renders with no page error and no horizontal scroll at 1440 and 390 px; Copilot ask → marks | suite green with the UI tests; matrix rows they cover cite them |
| **R1 design system 2.0** | tokens (board look), icons, components: stat card with a small chart, donut, ring, gauge, spark bars, progress bar, chip, news card, section head; header with tagline, search (R-D5), bell; applied to every new page | all new pages restyled; design_system.md rewritten; search and bell tested |
| **R2 Toàn cảnh to the board** | Pulse cards with real small charts (R-D3); Wealth Map as donut + legend + drill-down; Sankey with category icons, gradient bands, ratios, moving dashes on the selected band only; feed as impact cards; goals card with funding bars | every number traced to an API field (test); old Toàn cảnh content all present |
| **R3 old pages rebuilt** | Chi tiết, Tài sản (incl. statement upload and declaration chat), Kế hoạch, Khẩu vị rủi ro, Chi phí chính sách, Chuyên gia + Duyệt đề xuất, Hiệu quả tư vấn (client and RM) as module pages; `app.js`, `app.css`, `charts.js`, `fmt.js` removed; ADR supersedes ADR-0013 | per-page checklist ticked in `docs/brd/ux/screens/`; flows of FEAT-20…28 driven in the browser tests |
| **R4 graph and timeline** | overview graph (R-D6) with risk, source and goal nodes, expand/collapse, node → page; News Impact side panel (related news, chain, affected assets); event timeline on Tác động tin; CIO whole-run graph | every node/edge from a stored record (tests); keyboard and list alternatives |
| **R5 Copilot 2.0** | answers carry as-of time and sources; structured cards (figures, lists with chips, small charts) in the panel; tools `dieu_tra` (an event's path from the graph) and `kich_ban` (a stress scenario through `scenario_flow`); every call in the audit log; suggestion chips as on the board | tests: timestamps, new tools' results equal the graphs', audit rows, barrier unchanged |
| **R6 live demo** | models per R-D7 in the live `.env`; `scripts/demo_walkthrough.py` (fetch → events → agent → challenger → approve → runs, over HTTP); verify on the public URL | live pages show real runs; agent runs labelled with their models |
| **R7 regression and report** | all routes × 2 devices × 2 themes; Living Interface measurements again; matrix, CHANGELOG, PRODUCT_OVERVIEW; final report | report separates verified / unverified / partial / blocked |

After R7, `docs/BACKLOG.md` continues: B-02 newsletter (FR-801), B-03 policy agent (FR-306), B-04 FR-701 rest and
RULE-AI-02, B-05 remaining Copilot tools; plus BRD gaps not in the backlog yet: admin screen (RULE-ROLE-04), RM sees
own families only (Q-17), re-ask triggers for the risk test (Q-16), alerting on failures (NFR-12).

## 4. Status

| Phase | State | PR |
|---|---|---|
| R0 | done 2026-10-16: 6 browser tests (every route × 2 sizes, Copilot) in the suite, control checked | #32 |
| R1 | done 2026-10-16: tokens, header (search, bell), icons, small charts, controls, Copilot button; FEAT-34 | #33 |
| R2 | done 2026-10-16: Toàn cảnh as on the board; 3 browser tests | #34 |
| R3 | done 2026-10-16: the 8 pre-redesign pages rebuilt as module pages, app.js/app.css/charts.js/fmt.js deleted, shell owns client/scope/reset, per-route render host, UI files revalidated (`no-cache`); ADR-0019; 5 flow tests | #35 |
| R4 | done 2026-10-16: Bản đồ tài chính (overview graph, `POST /api/overview`), News Impact panel, event timeline, CIO run graph (`GET /api/runs/{id}/graph`); 9 tests | #36 |
| R5 | done 2026-10-16: Copilot 2.0 — as-of and sources, cards (figures, list, bars, chain), `dieu_tra` and `kich_ban`, every call audited, suggestion chips, followed goals; 6 tests | #37 |
| R6 | done 2026-10-16: live models on the public demo (CIO Sonnet 5.5, challenger Gemini 3.8 Flash, Copilot router Haiku 5.5); `scripts/demo_walkthrough.py` filled it from fetched news (2 runs in effect, 1 view pending); 154 k tokens | #38 |
| R7 | done 2026-10-16: every route × 2 sizes × 2 themes in the suite; Living Interface re-measured; approved-view checklist fixed; [report](UI_REDESIGN_REPORT.md) | #39 |

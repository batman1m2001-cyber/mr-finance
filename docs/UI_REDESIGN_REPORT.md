# OneWealth — UI redesign: final report (R7)

2026-10-16. The plan is [UI_REDESIGN_PLAN.md](UI_REDESIGN_PLAN.md) (PR #31). It answers the owner's request to
redraw the whole interface to the redesign kit's concept board and to recheck everything that had been missed.
Phases R0–R6 were merged as PRs #32–#38; this report and the R7 fixes are #39. All of it is live at
https://oneweath.ngrok.app.

Status words follow the traceability matrix:
- **verified**: a test in the suite checks it.
- **unverified**: built and checked by hand or by screenshots, with no suite test.
- **partial**: some of it is built.
- **blocked**: it needs something we don't have.

## 1. The gaps the audit found, and where they stand

| # | Gap (plan §1) | Status | Evidence |
|---|---|---|---|
| G1 | The 8 pre-BRD pages kept the old look | **verified** | Rebuilt as module pages: Chi tiết, Tài sản, Kế hoạch, Khẩu vị rủi ro, Chi phí chính sách, Chuyên gia / Duyệt đề xuất, Hiệu quả tư vấn (one client and all clients). Every block and action is kept. Each flow is driven in `tests/ui/test_pages.py` (R3, #35) |
| G2 | No board visuals | **verified** | KPI cards with small charts, donut, coloured Sankey with icons and ratios, impact cards, goals card (R2, #34); header search and bell (R1, #33). Every Toàn cảnh figure is traced to an API field (`tests/ui/test_pulse.py`) |
| G3 | Graph without sources, risks, expand, overview, node → page, CIO run | **verified** | Bản đồ tài chính overview with sources, risks, goals, policy items and news: expand/collapse, node → page, list view. CIO whole-run graph. Every edge resolves to its record (`tests/test_overview.py`, `tests/test_graph.py`; R4, #36) |
| G4 | No motion along cash flows, no view transitions | **partial** | Dots run along a picked Sankey band. They use transform only, pause with a hidden tab and stop under reduced motion (R2). There are no animated transitions between views or for expand/collapse: the graph redraws in place |
| G5 | No timeline | **verified** | Tin tác động shows each event's steps, from first news to "effective", with the times stored on their records (`tests/test_graph.py::test_the_timeline_reads_each_step_from_its_record`) |
| G6 | Copilot without times, sources, cards, investigate/analyze, audit | **verified** | Answers carry as-of, answer time, sources and a card. `dieu_tra` and `kich_ban` tools; every call is a row in the audit chain (`tests/test_copilot.py`, R5, #37). The live router is on a real model (R6) |
| G7 | Old frontend not separated | **verified** | `web/app.js`, `app.css`, `charts.js` and `fmt.js` are deleted (ADR-0019 supersedes ADR-0013). `tests/test_web.py::test_every_page_is_a_module_page` keeps it that way |
| G8 | Live demo on mock agents, empty | **unverified** | Real models: CIO agent `anthropic/claude-sonnet-5.5`, challenger `google/gemini-3.8-flash`, Copilot router `anthropic/claude-haiku-5.5`. `scripts/demo_walkthrough.py` filled the demo from fetched news: 3 live views, 2 in effect for every family, 1 waiting for the CIO, 154k tokens. Checked by screenshots; a live-model run is not part of the suite |
| G9 | No browser tests | **verified** | `tests/ui/` (Playwright, 22 tests): every route of every role at 1440 and 390 px, in light and dark; no page error, error panel or horizontal scroll; the flows of each rebuilt page; the Copilot's states, marks and cards |

## 2. The owner's requirements (OWN-UI)

| ID | Requirement | Status |
|---|---|---|
| OWN-UI-01 | Every page in the board's look | verified |
| OWN-UI-02 | Pre-BRD pages rebuilt, every block and action kept | verified |
| OWN-UI-03 | Header search and notifications | verified |
| OWN-UI-04 | Graph overview, timeline, CIO run graph | verified |
| OWN-UI-05 | Copilot with as-of and sources, cards, investigate and analyze, audited | verified |
| OWN-UI-06 | Live demo on real models with real runs | unverified (see G8) |
| OWN-UI-07 | Browser tests for every route and the main interactions | verified |

Across the matrix, 15 rows are still `implemented_unverified` (it was 14 when the audit found that browser tests
alone were missing). The rows R0–R6 could test moved to verified. Two kinds remain:
- rows where only a person can judge: a sense of presence (OWN-MOTION-01), "calm" (OWN-MOTION-05), KIT-UX-06;
- rows that need a live environment: OWN-UI-06 and the BRD's news-to-run timings.

## 3. Regression and measurements (R7)

- **Suite:** 254 tests pass (`pytest`), 22 of them browser tests, about 4 minutes. The doc checker passes.
- **Every route** of every role (36 routes) renders on desktop and phone, in light and dark, with no page error,
  error panel or horizontal scroll (`tests/ui/test_routes.py`, 4 runs).
- **Living Interface**, re-measured with the B-01 script and page (FEAT-33):
  - At rest with the panel closed: unchanged at 1.4 ms of main-thread time per 5 s, with no style work and no
    animation.
  - One Copilot question: 170 ms, up from 144 ms. The answer now draws a card and its sources; the cause was not
    isolated further. No long task.
  - Every animation pauses with a hidden tab; only transform and opacity animate.
  - The page loads 62 KB of JS, down from 135 KB, and 56 KB of CSS, up from 29 KB because one stylesheet now
    serves every page.
- **Fixed in R7:** an approved view's approval checklist showed a red ✕ "Đang chờ duyệt". A decided view now
  shows "đã quyết: Đã duyệt" and only the conditions that still apply.

## 4. Known limits (stated on the pages, not faked)

- **No net-worth history.** The board's trend line is replaced by the month's change split by asset class.
- **No investment flows in the transactions.** The Sankey has no "Đầu tư" band.
- **Overview graph:** with every kind switched on (about 35 nodes) a few labels still touch. Sources and policy
  items start hidden. Holdings are joined to risks and policy items by name.
- **Mock agent:** it builds its summary from the headlines, so a headline with an action word ("bắt đáy") fails the
  content rule and the view ends in AGENT_ERROR. The guard holds; the live agent is prompted not to use such words.
- **The client's numbers:** the client sees impact by asset class only (ADR-0008), so "every number has cách tính"
  (NFR-11) stays a staff feature (Q-14).

## 5. What comes next

The backlog continues (`docs/BACKLOG.md`):
- B-02 newsletter (FR-801);
- B-03 policy agent (FR-306);
- B-04 the rest of FR-701 and RULE-AI-02;
- B-05 the remaining Copilot tools (research release, news dismiss/release, declarations).

BRD gaps not yet in the backlog:
- the admin screen (RULE-ROLE-04);
- an RM sees only their own families (Q-17);
- re-ask triggers for the risk test (Q-16);
- alerting on failures (NFR-12).

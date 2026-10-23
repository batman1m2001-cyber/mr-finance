# Open questions, ambiguities, conflicts and divergences — `Q-nn`

Each entry separates **what the sources say** (fact) from **our interpretation** (proposal) and records who
can decide. A resolved entry stays here with its resolution; it is never deleted.

Types: **ambiguity** (a source is unclear) · **conflict** (two statements disagree) · **divergence** (the
product differs from a source, knowingly) · **gap** (required, not built — found during documentation).

| ID | Type | Topic | State |
|---|---|---|---|
| Q-01 | divergence | The BRD describes its author's TypeScript/Cloudflare demo; this product is Python/operonx | resolved (ADR-0002) |
| Q-02 | ambiguity | The BRD's own open decisions (content boundary, model parameters, AI infrastructure) | open — business |
| Q-03 | conflict | BR-08 “one engine for alerts” vs the product's separate policy-cost alerts | resolved for this phase (ADR-0007; the card relabelled in F10); presets N5 remain |
| Q-04 | conflict | BRD §3 puts Open API and statements out of scope; the product has them | resolved (ADR-0003) |
| Q-05 | ambiguity | What makes the challenger “independent, 2nd line” | open |
| Q-06 | divergence | The kit's Copilot, Money Flow and graph are not in the BRD; the Copilot as worded conflicts with BR-11 | resolved for planning (ADR-0012) |
| Q-07 | ambiguity | KPI-02 “important news” is undefined | open — business |
| Q-08 | ambiguity | FR-101 “10 sources” vs §11.1's list | resolved (interpretation) |
| Q-09 | ambiguity | FR-306 “radar chính sách” is undefined | open — business |
| Q-10 | ambiguity | FR-402 “chi phí lãi vay” | open |
| Q-11 | ambiguity | FR-404 level thresholds and funding source are undefined; built on our proposal | resolved (ADR-0017) |
| Q-12 | conflict | FR-501 “the challenger writes the summary” vs F02 / §7.1 | resolved (BRD F02) |
| Q-13 | conflict | NFR-05 exact decimals vs the BRD's own float engine (F22) | resolved (ADR-0011) |
| Q-14 | conflict | NFR-11 “every number has cách tính” vs flow 2 (no tickers to clients) | resolved (FEAT-09, G1) |
| Q-15 | conflict | §13.1 two-person rule: sentence vs ownership table | resolved for the demo (ADR-0016) |
| Q-16 | gap | Brief: re-asking the risk test on triggers | open |
| Q-17 | gap | RM sees only their own families: the demo has one RM and no assignment | resolved (ADR-0020) |
| Q-18 | divergence | 20 mock families (BRD) vs 5 clients + 2 spouses here | resolved (ADR-0005); a 1,000 / 6,500 Private book proposed (ADR-0038) |
| Q-19 | divergence | The advisory track record is mock and could be read as BR-15 | resolved (labelled; dates fixed) |
| Q-20 | gap | FR-603 “tab Mục tiêu”: the goal branch is not on the client's Goals/Plan tab | resolved (shown on Kế hoạch) |
| Q-21 | divergence | The client view exists although the BRD puts client delivery in the pilot phase | resolved (ADR-0008) |
| Q-22 | divergence | Factor-model parameters are assumed, not estimated | resolved (ADR-0004); estimation blocked |
| Q-23 | divergence | One process instead of a separate AI zone; no signed inbox | resolved for the demo (ADR-0009) |
| Q-27 | ambiguity | Whose book the test data is: Private only, or Private and Priority | resolved (the submission: Private only; ADR-0038); licence open |

---

### Q-01 — Two implementations of the same BRD
- **Fact:** The BRD describes a demo on TypeScript, Hono, Cloudflare Workers and D1 (28 tables, ~80 endpoints), React, LangGraph, Zod, decimal.js, 20 mock families, 143–160 tests (§1, §11.4, §12.1, §16.1, §20). Its “Demo” column in §4 reports that demo.
- **Fact:** This repository implements the BRD in Python on operonx (graphs, services, jobs), SQLite, no-build ES modules; the product owner confirmed it must stay on operonx.
- **Resolution:** [ADR-0002](../decisions/ADR-0002-implement-the-brd-on-operonx-not-the-brd-stack.md). The BRD's requirements apply; its stack and counts do not. Our status is only ever in the traceability matrix.

### Q-02 — Decisions the BRD itself leaves open
- **Fact (§1):** “Việc cần quyết định để đi tiếp: chốt ranh giới nội dung gửi khách với Pháp chế và Tuân thủ; CIO xác nhận thư viện cú sốc và tham số mô hình; chọn hạ tầng AI trong môi trường được duyệt để thí điểm.” Also §14 (three flows to be fixed with Legal and Compliance before the pilot) and §15 (NFR figures to be confirmed by Technology and Information Security).
- **Owner:** Private Banking, Legal, Compliance, CIO, Technology. Not resolvable in this repository.

### Q-03 — One engine (BR-08) vs policy-cost alerts
- **Fact:** BR-08: the engine is “bộ máy duy nhất cho xếp hạng, cảnh báo, mục tiêu và diễn giải”.
- **Fact:** The product also has `alerts_flow` (src/impact, from the brief): 19 dated factors (14 policies, 2 macro moves, 3 infrastructure projects) scored as exposure × sensitivity × probability. Some are cash costs (property tax, transfer tax, PIT), some are price moves (gold-bar policy, market upgrade, FX, metro).
- **Resolution (partial), [ADR-0007](../decisions/ADR-0007-policy-cost-alerts-stay-outside-the-engine.md):** cash-cost rules are not price moves and stay as “Chi phí chính sách”, outside the ranking. Price-moving rules should become engine presets (planned, news plan N5).
- **Visible inconsistency (2026-10-15):** the client overview's “Headline News” card ([SCR-CL-01](../assets/current_ui/SCR-CL-01_desktop-light.jpg)) shows the old point-rule numbers (e.g. “Metro số 1 … +778 triệu”), while “Tin tác động” ([SCR-CL-05](../assets/current_ui/SCR-CL-05_desktop-light.jpg)) shows the engine's (“−726 triệu”). Two “news” numbers from two methods, side by side in one product. Proposed: the overview card links to the engine's result, and the point rules are labelled as policy costs. Owner: product.
- **Done (F10, 2026-10-16):** the overview card is “Chính sách và dự án”, says its numbers come from each policy's own rules (tax, fees, project zones), not the scenario engine, and links to Tác động thị trường for the news impact; goals now get the engine's VND impact (BR-08). Turning the price-moving rules into engine presets (N5) stays for a later phase.

### Q-04 — Open API and statements
- **Fact:** BRD §3 lists “Kết nối dữ liệu tài sản ngoài hệ sinh thái TCB (Open API, sao kê)” as out of scope *for this phase*, belonging to step 1 of the Wealth AI journey. The brief (BRIEF-DATA-02) requires both, and they are built.
- **Resolution:** [ADR-0003](../decisions/ADR-0003-keep-the-capabilities-that-predate-the-brd.md). “Out of scope of the BRD's module” is not a prohibition; the capabilities are kept, documented as brief features.

### Q-05 — Independence of the challenger
- **Fact:** BR-06 requires a challenge “độc lập bởi tuyến 2”; §8 makes the challenger an AI owned by Compliance, using a different model from the CIO agent; F11 blocks approval when the challenge came from the same session.
- **Fact:** In this product, approval condition *f* is “challenger independent”: in live mode two different configured models; in mock mode the challenger is a rule set (`src/views/challenger.py`), which condition *f* accepts as independent.
- **Interpretation (ours):** a rule set shares no failure mode with a keyword drafter, so the mock run is treated as independent; a real deployment needs the challenger in a separate environment (BRD F11 “Còn lại”). Owner: Compliance.

### Q-06 — The kit's additions and BR-11
- **Fact:** The BRD mentions no chat assistant, Sankey or relationship graph. The kit asks the Copilot to “answer questions using authorized application data”.
- **Fact:** BR-11, §7.1, §14 and NFR-08 forbid sending client data to an AI provider.
- **Resolution (for planning):** [ADR-0012](../decisions/ADR-0012-the-copilot-routes-and-never-reads-client-data.md): the model routes, never reads. Money Flow and the graph are built only from stored records. All are **proposed extensions** (Layer A: [kit_requirements.md](kit_requirements.md)).

### Q-07 — “Important news” (KPI-02)
- **Fact:** “Tin quan trọng được thu thập ≥ 95 %” — the BRD does not define important news or how to count the denominator. Owner: CIO / Private Banking.
- **Interpretation (ours, applied; G-D6, labelled “Đề xuất”):** important = a story in an independent reference
  (Google News' Business section for Vietnam) whose title names one of the engine's factors and that ≥ 2 outlets
  carry; collected = one of our items matches it by title, judged once a day later (`src/news/reference.py`). The
  same reading defines urgent for KPI-01: the CIO's flag, with the product's proposals (`src/news/urgent.py`).

### Q-08 — How many sources (FR-101)
- **Fact:** FR-101 says “hiện 10 nguồn: VnExpress, VnEconomy, Báo Đầu tư, Vietstock, Nhân Dân, VTV, Fed…”; §11.1 lists six domestic and two international outlets.
- **Interpretation (ours, applied):** the number is the author's demo's; the requirement is “every configured white-listed source, every 10 minutes”. The product configures 11 feeds (`data/news_config.json`, NEWS-DEMO-2026-10); on 2026-10-15 Báo Đầu tư, Nhân Dân and VTV returned no items and were left out of the white list, as recorded in the news plan §9.

### Q-09 — “Radar chính sách” (FR-306)
- **Fact:** only the words. Not built. Owner: Compliance.

### Q-10 — Loan interest cost (FR-402)
- **Fact:** FR-402 lists “chi phí lãi vay”; §9.3 says a floating VND loan is sensitive to the VND rate as “chi phí lãi tăng thêm mỗi năm”.
- **Fact:** the product's family result has `loan_interest_3m` = the sum of the loan holdings' 3-month contributions (`src/apply/run.py`).
- **Open:** whether the BRD wants the extra annual interest cost as a separate figure. Owner: CIO.

### Q-11 — Goal impact per run (FR-404)
- **Fact:** FR-404 requires, for each run, each goal's funding ratio before and after, with a level Đạt / Theo dõi / Thiếu. The thresholds are not given.
- **Gap found 2026-10-15:** application runs do not compute goal impacts (`src/apply/run.py` has no goal step; there is no `goal_impacts` table). The news plan reported FR-401…406 as done in N3; FR-404 was not. Corrected in the matrix and in `docs/NEWS_IMPACT_PLAN.md` §9.
- **Existing related capability:** goals planning (FEAT-26) computes each goal's need, what the client has for it (a funding share), and ON_TRACK / AT_RISK / OFF_TRACK from the monthly saving needed ÷ the monthly surplus (≤ 0.6, ≤ 1, above; `src/scenarios/_sim.py::goal`).
- **Proposal (ours):** for each goal, apply the run's 3-month expected change to the assets set aside for it, recompute the funding share and the status before and after, and map Đạt = ON_TRACK, Theo dõi = AT_RISK, Thiếu = OFF_TRACK. Owner: CIO to confirm the mapping and thresholds.
- **Built 2026-10-15 on this proposal** (`src/apply/goals.py`): no asset is earmarked in the data, so the dated goals draw in date order on the family's financial assets (cash, deposits, funds, bonds, stocks, gold, crypto). Consequence: for the five demo families every goal is 100 % funded and Đạt before and after (C01: 14.7 tỷ of such assets against 1.885 tỷ of goals). Still open: the funding source and the thresholds.
- **Resolution 2026-10-16:** the owner left the choice to us (D-02); the rule above is kept and recorded in
  [ADR-0017](../decisions/ADR-0017-goal-impact-rule.md), which says why the goals-planning pool was not used.

### Q-12 — Who writes the post-check summary (FR-501)
- **Fact:** FR-501 says “Agent Phản biện viết tóm tắt”; the BRD's own F02 says explanations and the post-check summary use deterministic templates, and §7.1 forbids family data in the AI zone.
- **Resolution:** follow F02; the product's summary is a template (`postcheck()` returns `"by": "rules"`).

### Q-13 — Exact money (NFR-05)
- **Fact:** NFR-05 forbids floating point for balances; F22 records that the BRD's scenario layer uses floats, rounded to the dong, recomputing exactly from the snapshot.
- **Resolution:** [ADR-0011](../decisions/ADR-0011-engine-in-floats-rounded-to-the-dong.md): balances are integers; the engine computes in floats and rounds every VND result once; contributions use largest-remainder rounding so they add up exactly.

### Q-14 — “Cách tính” for every number vs no tickers for clients
- **Fact:** NFR-11: every number has a “cách tính” button. Flow 2 (§14): client content has no ticker names.
- **Fact:** the trace (FR-406) names holdings, so the product shows it to staff only; the client sees the formula sentence and the asset-class breakdown but no trace button ([SCR-CL-05](../assets/current_ui/SCR-CL-05_desktop-light.jpg)).
- **Open:** a client-level “cách tính” at asset-class granularity. Owner: product + Compliance.
- **Resolved 2026-10-16 (F10, G1):** both. The client has its own “cách tính” of a news-impact number by asset class (F-D9), and since G1 every money or percent figure of every page, for every role, opens its formula and inputs from one catalogue ([FEAT-09](../features/FEAT-09-number-trace.md)); the holding-level trace stays staff-only, so flow 2 holds.

### Q-15 — Two-person rule
- **Fact:** §13.1 sentence: “cần hai người cho prompt, mô hình AI, mô hình yếu tố, ngưỡng cảnh báo và danh sách hạn chế”. §13.1 table: two people only for prompts and AI models; thresholds, factor model, restricted list “Không”. F14 says the factor model, thresholds and restricted list *were changed* to need two people.
- **Resolution (2026-10-16, ADR-0016):** follow the sentence and F14 (stricter): two people for the factor model, thresholds and restricted list; Compliance may relax it.

### Q-16 — Re-asking the risk test
- **Fact:** BRIEF-RISK-04 asks the system to re-ask on life changes, market moves or every 6 months. The product compares what the client says with what they did (April dip), but has no re-ask trigger. Owner: product.

### Q-17 — RM sees only their own families
- **Fact:** BRD-RULE-ROLE-02 and §13.1. The demo has one RM user (`rm01`) and no family assignment; every RM read returns every family. Building it needs an assignment table and a check in each RM read. Planned with FR-701-style configuration; owner: product.
- **Resolved 2026-10-16:** three RMs sign in with their own accounts and see only the families assigned to them (`people.rm_id`); [ADR-0020](../decisions/ADR-0020-sign-in-with-own-accounts.md).

### Q-18 — Number of families
- **Fact:** the BRD's demo has 20 mock families; here 5 clients and 2 spouses (household scope). Ranking and BR-09 work at any count. [ADR-0005](../decisions/ADR-0005-mock-clients-and-prices-public-news.md).
- **Proposed (2026-10-23):** the demo stays; a second client set of 1,000 Private clients (6,500 for the book), converted from Santander's public data, for the KPIs and NFR-01 ([ADR-0038](../decisions/ADR-0038-a-second-client-set-the-santander-vn-private-book.md), [Q-27](#q-27--whose-book-the-test-data-is)).

### Q-19 — The advisory track record
- **Fact:** “Hiệu quả tư vấn” ([SCR-RM-05](../assets/current_ui/SCR-RM-05_desktop-light.jpg)) shows recommendations, accuracy (75 %), money gained/lost, missed news and AI pipeline scores, from `data/advisory.json` (mock, labelled “Dữ liệu giả định cho demo”). Some entries are dated after the demo's date (e.g. 2026-10-24 when the data is as of 2026-10-09).
- **Risk:** it can be mistaken for BR-15 (accuracy over time; built since F3 as FEAT-18 on real market data). Proposed: say on the page that it is illustrative and is not BR-15; fix the dates. Owner: product.
- **Resolution (2026-10-15):** the page note now says “minh họa, không phải số liệu theo dõi độ chính xác của nhận định”; dates clamped to the data date (DEF-05, `tests/test_app.py::test_nothing_in_the_advisory_record_is_dated_after_the_data_date`).

### Q-20 — The goal branch on the Goals tab (FR-603)
- **Fact:** FR-603: show on the RM home, the Goals tab, and the Research page. The product shows it on RM “Hôm nay”, on “Tin tác động” (client and RM) and on “Nghiên cứu”. The client's “Mục tiêu & kịch bản → Kế hoạch” tab (goal planning) does not show it.
- **Resolution (2026-10-16):** the planning tab shows “Lưu ý quy định cho mục tiêu” above the goals (client: only notes with a client message; staff: every match).

### Q-21 — A client view before the pilot
- **Fact:** §3: the client interface belongs to the pilot. The product has a client role (it predates the BRD).
- **Resolution:** [ADR-0008](../decisions/ADR-0008-the-client-sees-asset-classes-only.md): the client sees only effective, post-checked results, at asset-class level, event type instead of headline, the AI label and “không phải khuyến nghị”.

### Q-22 — Assumed model parameters
- **Fact:** the BRD estimates volatilities and correlations from 55 months of history; we have no Vietnamese history series. [ADR-0004](../decisions/ADR-0004-assumed-factor-model-parameters.md). Estimating them is **blocked** on data (VN-Index, foreign flows, SJC spread, VN rates history).

### Q-23 — No separate AI zone
- **Fact:** §7.1 requires a separate zone, its own DB, a write-only signed inbox. The product runs in one process. [ADR-0009](../decisions/ADR-0009-ai-barrier-by-graph-inputs-in-one-process.md): the barrier is enforced by the agent graphs' inputs and tested; the signed inbox (and FR-307's inbox mode) is planned.

### Q-24 — Which roles the multi-role request covers
- **Fact:** the owner's request (2026-10-18, OWN-MR) names CIO, RM, Admin and Expert. The product has no role called
  Expert; it has `specialist` ("Chuyên gia", BRD-RULE-ROLE-05: approves action recommendations for assigned families).
  It also has Compliance (BRD-RULE-ROLE-03), which the request does not name, while its completion criterion says
  "every role has a coherent, role-appropriate UX".
- **Interpretation (ours):** Expert = `specialist`; Compliance gets a desk too, last (plan M5). Owner: product.
- **Answered (owner, 2026-10-18):** "yes, expert is the specialist, and yes, compliance also need refine". Both
  applied: the Expert's desk (SCR-SP-02) and Compliance's (SCR-CMP-06).

### Q-25 — Admin's "user and role management"
- **Fact:** the request lists "user and role management" for Admin. BRD-RULE-ROLE-04 gives Admin news sources, data
  loading, operations, configuration and system status. The product shows Admin every staff account and role and the
  RM assignment (a configuration Admin owns, two-person); it deliberately has no form to create users or set
  passwords on the public demo (a visitor could lock others out; SCR-ADM-01, `scripts/set_password.py`).
- **Interpretation (ours):** the Admin desk shows people and roles and opens the assignment; no account or password
  form is added (it would be a new capability and a demo risk). Owner: product.
- **Applied (M3, 2026-10-18):** SCR-ADM-02 shows people by role and accounts without a password, links the RM
  assignment on Cấu hình; still no account form. OWN-MR-04 partly met until answered.
- **Owner's answer (2026-10-18):** “do it, add the feature you think it's best for it”.
- **Applied (U, 2026-10-18; [OWNER_BACKLOG_1018_PLAN.md](../../OWNER_BACKLOG_1018_PLAN.md)):** SCR-ADM-03 Tài khoản
  và vai trò. Admin adds a staff account, changes a role, disables or enables an account, or resets a password; each
  is a request one Admin files and a second Admin approves (the proposer cannot, nor can the subject), every step in
  the audit chain. No password is ever typed by Admin: an approved add or reset shows a one-time code once (24 hours,
  kept only as a hash), which the person redeems on the sign-in page to set their own. Disabling ends a live session
  at its next request; a role change is read at the next request. Guards: never one's own account, never the last
  enabled Admin, never an RM who still has families (move them first on Cấu hình › Phân công RM, two-person), never
  a customer's account (they follow the family's record), and the demo's own personas stay as they are while
  `MF_DEMO_ACCOUNTS` is on (so the public demo cannot be locked). The assistant files the same requests on a Xác
  nhận (`yeu_cau_tai_khoan`) and never approves. OWN-MR-04 met.

### Q-26 — How much of a family a specialist sees
- **Fact:** BRD-RULE-ROLE-05 says the specialist approves recommendations for assigned families; it says nothing on what
  they read. `people.auth.may_see` already lets a specialist read the families assigned to them (their reads are the
  family-scoped ones; `/api/trace/` and the staff-only reads stay closed to them).
- **Interpretation (ours):** the Expert desk shows, beside a recommendation, what the specialist may already read of
  that family (net worth, allocation, risk profile, goals), through the existing reads; nothing more. Owner: Compliance.
- **Applied (M4, 2026-10-18):** SCR-SP-02 reads the picture through `POST /api/dashboard` and `/api/goals` (family
  scope), which already answer a specialist for an assigned family only; the assistant's `ho_so_khach` refuses any
  other family. Nothing new is opened to the role.
- **Owner's question (2026-10-18): "what does the original BRD describe?"** The BRD defines the specialist only by
  what they decide, never by what they read: ROLE-05 ("approves action recommendations for assigned families"),
  CONTENT-01 flow 3, SCOPE-02 (no single-ticker recommendation straight to a client), WF-08. SEC-01 ("least privilege
  by role and assigned families") is the only rule on reading. The reading above follows SEC-01. Still open for
  Compliance to widen or narrow.

### Q-27 — Whose book the test data is
- **Fact:** the challenge is set in Private Banking ("a Wealth Platform … for private clients"). Our submission
  (`nop_bai_cuoc_thi.md` §4, §5.1) sizes the product on about 6,500 Private clients (88 % coverage ≈ 5,700) and
  leaves Priority to a later, reduced version (months 13–24); its §5.8 assumes ≈ 60 tỷ total wealth per client,
  ≈ 35 % at TCB. The BRD's NFR-01 counts 6,500 families.
- **Fact:** the first draft of [`docs/CLIENT_DATASET_PLAN.md`](../../CLIENT_DATASET_PLAN.md) mapped Santander's
  PARTICULARES to Priority and drew 15 % Private — a sample-size choice with no source.
- **Resolution (2026-10-23):** the book is Private only, drawn from Santander's TOP and tiered by income; Priority
  enters only as an optional, labelled "Priority đủ ngưỡng lên Private" group
  ([ADR-0038](../decisions/ADR-0038-a-second-client-set-the-santander-vn-private-book.md)). Owner: product.
- **Open:** the Santander competition rules (D0), the tier cut-offs (giả định 30 / 55 / 15 %), and the real figures
  that replace the submission's 60 tỷ / 35 %. Owner: product, Private Banking.

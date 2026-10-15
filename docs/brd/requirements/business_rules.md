# Business rules stated in the BRD without a code — `BRD-RULE-<area>-nn`

Layer A. Most of the BRD's precise rules are not in its BR/FR/NFR tables: they sit in the prose and tables of
§3, §5, §7–§11, §13, §14 and §16. They are extracted here so that each can be traced and tested. Each row quotes
or closely paraphrases the BRD at the stated location; nothing here is our invention. Where a rule describes
only the author's stack (a library, a cloud product), it is not a rule and is listed in
[`original_brd_reference.md`](original_brd_reference.md) instead.

Status per rule: [`requirements_traceability.md`](requirements_traceability.md) §2.

## SCOPE — what is in and out (§3)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-SCOPE-01 | §3 “Ngoài phạm vi” | No order placement, money transfer or any automatic transaction | documented |
| BRD-RULE-SCOPE-02 | §3; §14 flow 3 | No buy/sell recommendation of a single ticker goes straight to a client; always through a certified specialist | documented |
| BRD-RULE-SCOPE-03 | §3 | Connecting asset data outside TCB (Open API, statements) is out of scope for this phase (“thuộc Bước 1 của Trợ lý Wealth AI”) | needs_clarification (Q-04: the product already has these, from the brief) |
| BRD-RULE-SCOPE-04 | §3 | No valuation of individual properties from real transaction prices | documented |
| BRD-RULE-SCOPE-05 | §3 | The client interface and real sending of content to clients belong to the pilot phase | documented |

## ROLE — who does and sees what (§3 table, §13.1)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-ROLE-01 | §3 roles | CIO: runs the CIO agent, edits and approves views; owns the factor model and thresholds; uploads research. Sees events, views, and every client's results after approval | documented |
| BRD-RULE-ROLE-02 | §3; §13.1 | RM: sees impacts and procedural notes of **their own** families only, and only post-checked results; enters goals; writes notes. Opening another RM's family is refused | documented |
| BRD-RULE-ROLE-03 | §3 | Compliance (2nd line): releases research; approves white and restricted lists; owns the challenger and policy agents; traces. Sees everything, with the log | documented |
| BRD-RULE-ROLE-04 | §3 | Admin: news sources, data loading, operations. Sees configuration and system status | documented |
| BRD-RULE-ROLE-05 | §3 | Certified specialist (later phase): approves action recommendations for assigned families | documented |
| BRD-RULE-ROLE-06 | §3 | Client (later phase): sees updates and notes on goal cards — own family only, approved content only | documented |

## WF — the workflow and its time targets (§5, Figure 1)

| ID | Source | Step | Who | Time target | Doc status |
|---|---|---|---|---|---|
| BRD-RULE-WF-01 | §5 step 1 | Fetch news, label the source, filter white and restricted lists | Machine | ≤ 10 min after publication | documented |
| BRD-RULE-WF-02 | §5 step 2 | Group news into an event; run the CIO agent | CIO | Business hours | documented |
| BRD-RULE-WF-03 | §5 step 3 | Analyse, debate, write view and scenarios | CIO agent | ≤ 15 min | documented |
| BRD-RULE-WF-04 | §5 step 4 | Raise findings by severity | Challenger | ≤ 5 min | documented |
| BRD-RULE-WF-05 | §5 step 5 | Edit scenarios, answer findings, approve or return | CIO | CIO SLA | documented |
| BRD-RULE-WF-06 | §5 step 6 | Compute every family, post-check, rank, flag RM cases | Machine | ≤ 5 min | documented |
| BRD-RULE-WF-07 | §5 step 7 | Look at severe cases first, contact clients | RM | Same day | documented |
| BRD-RULE-WF-08 | §5 step 8 | Approve action recommendations, if any | Specialist | Advisory process | documented |
| BRD-RULE-WF-09 | §5 | End to end ≤ 2 h; urgent ≤ 30 min. Family data enters the engine only after CIO approval; the AI part never touches client data (Figure 1 note) | — | ≤ 2 h / ≤ 30 min | documented |

## ZONE — AI outside, results in (§7, §7.1, §11.4, §13.2)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-ZONE-01 | §7.1; §13.2 | Every AI assessment runs in a separate zone outside TCB with its own database, holding only: public news, released research copies, factor catalogue and shock library, instrument catalogue (no quantities or owners), agent runs. No read account on the TCB database; no family, position, loan, goal, RM note or AML data | documented |
| BRD-RULE-ZONE-02 | §7.1 | The TCB inbox accepts new writes only and returns no data; the AI zone's service account has only that right; results arrive through a signed API | documented |
| BRD-RULE-ZONE-03 | §7.1 | Each result package passes the checks — format, probabilities, factors in the catalogue, source news belonging to the event, restricted list — before becoming a view awaiting the CIO. A bad package is refused with its error and changes no data | documented |
| BRD-RULE-ZONE-04 | §7.1; §8 table | After approval the engine runs inside TCB with family data. Explanations for RMs use deterministic templates or an in-bank model; client data never goes to the AI zone | documented |
| BRD-RULE-ZONE-05 | §7 | The AI, compute and control layers are separate: AI reads news and writes views; only the compute layer reads family data; every write goes through the control layer into the hash-chained log | documented |
| BRD-RULE-ZONE-06 | §7.1 table | TCB → AI zone: only released research (after Compliance release and its publication time) and approved factor-model and instrument-catalogue versions. AI zone → TCB: events, views, scenarios, challenges, run traces, signed and logged with the package hash. Client data: none, blocked by network and permissions | documented |

## AI — the agents and their controls (§8)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-AI-01 | §8 table | Four LLM tasks: CIO agent (owner CIO, risk High), Challenger (owner Compliance, Medium; model different from the CIO agent's), Policy agent (Compliance, Medium; sees no portfolio, draws no conclusion for a family), Internal explanation (CIO, Low; needs family data so runs inside TCB, template or in-bank model) | documented |
| BRD-RULE-AI-02 | §8 | Models and prompts are versioned configuration; a change needs two people (propose and confirm) | documented |
| BRD-RULE-AI-03 | §8 | No server-side fallback model: a reply from a model other than the approved one is refused | documented |
| BRD-RULE-AI-04 | §8.1 | CIO agent graph: deterministic data step (event news, catalogues, 15 factors, shock library) → four analyst groups in parallel (macro & rates; equities & funds; credit & real estate; commodities & other) → bull/bear debate only when a row is ±2 or more or groups disagree, ≤ 2 rounds → synthesis → format check, back to synthesis at most twice, then an error for the CIO | documented |
| BRD-RULE-AI-05 | §8.1 | Mandatory prompt rule: a stress scenario must put VN-Index and real-estate credit among its core shocks (lesson of the 2022 back-test) | documented |
| BRD-RULE-AI-06 | §8.2 | Output schema: `summary` (Vietnamese, no buy/sell words); `impacts[]` (asset class, sector, ticker, FX; level −3..+3, direction, horizon, confidence, rationale, sources); `scenarios.priced_in` (chưa / một phần / đã hết); `branches[]` 2–4, probability 5–95 %, sum 100 % ± 1.1 points, regime normal/stress; `core_shocks[]` 1–5 per branch, factor in the catalogue, size S/M/L, up/down; `rationale` ≥ 20 characters; `source_ids` must belong to the event | documented |
| BRD-RULE-AI-07 | §8.3 | Prompt-injection defence: all data in a prompt is wrapped in “DỮ_LIỆU … HẾT_DỮ_LIỆU” and the prompt says it is data, not instructions | documented |
| BRD-RULE-AI-08 | §8.3 | No invented numbers: AI only picks shock sizes from the library; the engine computes figures | documented |
| BRD-RULE-AI-09 | §8.3 | Schema validation before saving, in live and inbox modes alike | documented |
| BRD-RULE-AI-10 | §8.3 | Two different models for drafting and challenging | documented |
| BRD-RULE-AI-11 | §8.3 | Full trace: every step stores input, output, prompt, prompt version, model, time | documented |
| BRD-RULE-AI-12 | §8.3 | Token limit: a truncated output is an error; an incomplete reply is never used | documented |
| BRD-RULE-AI-13 | §8.4 | Live mode runs in the background through a job queue; inbox mode imports every 10 minutes through the same checks; mock mode = keyword scenarios, no AI, for automated tests | documented |
| BRD-RULE-AI-14 | §8; §11.4 | Every LLM task reads only news, documents, the factor model; it reads no family data and sends nothing out by itself | documented |

## ENG — the quantitative engine (§9)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-ENG-01 | §9 | Deterministic formula, no AI: the same inputs always give the same result | documented |
| BRD-RULE-ENG-02 | §9.1 step 1 | Priced-in multiplier on core shocks: not priced × 1, partly × 0.5, fully × 0. Sizes S/M/L come from each factor's library | documented |
| BRD-RULE-ENG-03 | §9.1 step 2 | Other factors by conditional expectation on the regime's covariance: Δn = Σnc Σcc⁻¹ Δc; residual Σn\|c = Σnn − Σnc Σcc⁻¹ Σcn | documented |
| BRD-RULE-ENG-04 | §9.1 step 2 | Band width has three parts: residual of inferred factors (monthly, × horizon 0.25 / 3 / 12 months); core-shock size uncertainty (σ = 40 % of the shock, propagated through correlation); idiosyncratic risk of directly held stocks (from R² against VN-Index) | documented |
| BRD-RULE-ENG-05 | §9.1 step 3 | Apply to each position by its sensitivity (§9.3) times each factor's realisation at the horizon | documented |
| BRD-RULE-ENG-06 | §9.1 step 4 | Branches combine as a probability-weighted normal mixture; percentiles P5 (very bad, reference only), P10 (bad), P50, P90 (good) at 1 week, 3 months, 12 months | documented |
| BRD-RULE-ENG-07 | §9.1 step 4 | The headline number for ranking, alerts, goals and explanation is the **3-month expected impact** (probability-weighted mean), so it adds up across positions, classes and factors | documented |
| BRD-RULE-ENG-08 | §9.1 | Stressed matrix: normal correlations × 1.4, clipped to ±0.85, four pairs overridden (VN-Index with foreign flows, FX, global equities, real-estate credit), then repaired to positive definite by eigenvalue clipping; stressed volatilities from 3–12/2022, at least 1.2 × normal | documented |
| BRD-RULE-ENG-09 | §9.1 | The model is checked before saving: correlations in [−1, 1], symmetric, positive definite | documented |
| BRD-RULE-ENG-10 | §9.2 | The 15 factors, their S/M/L sizes and their realisation at 1 week / 3 months / 12 months (table §9.2) | documented |
| BRD-RULE-ENG-11 | §9.2 note | Parameter provenance is labelled per factor (“Ước lượng” estimated from 55 months with 20 % shrinkage, “Giả định” assumed) | documented |
| BRD-RULE-ENG-12 | §9.3 | Sensitivities per asset class: VN equities (beta to VN-Index, sector beta when data is missing, USD-revenue share also to FX); foreign equities; bonds (modified duration + sector spread); funds (by contents); gold (world gold + FX + 0.9 × SJC spread); crypto; FX; property (house-price proxy, labelled “theo mô hình”); private equity (0.5 × VN-Index, labelled); USD loans (FX, inverse); floating VND loans (extra interest per year) | documented |
| BRD-RULE-ENG-13 | §9.4 | Worked example: world gold −5 %, inferred FX +0.3 %, SJC spread −0.5 point → SJC ≈ −5.15 %; 2 tỷ of SJC gold → about −103 triệu (illustrative numbers) | documented |

## GOAL — the goal branch (§10)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-GOAL-01 | §10 | The result is a date, documents and an urgency — never money. Inputs: released regulation notes and the family's active goals only | documented |
| BRD-RULE-GOAL-02 | §10 | Six purposes: study abroad; emigrate or retire abroad; invest abroad; buy property abroad; support relatives abroad; other transfer | documented |
| BRD-RULE-GOAL-03 | §10 | A declared outflow is used as declared. Undeclared: inferred from the goal's name, but an inferred match only creates an RM task (“RM xác nhận mục tiêu”), never a client message; names like “Nhật Minh”, “Mỹ Linh” must not be taken for countries; a personal name like “Minh Đức” must not match | documented |
| BRD-RULE-GOAL-04 | §10 | Milestone = first day of the month the money is needed − (extra preparation weeks + 4 weeks buffer) | documented |
| BRD-RULE-GOAL-05 | §10 | Past or closed goals are skipped | documented |
| BRD-RULE-GOAL-06 | §10 table | Levels: **contact now** (milestone ≤ 3 months away and the text issued) → RM calls; **remind on goal card** (spending within 104 weeks, or the text still a draft) → client sees a note, RM reminds; **note** (further out, or before the effective date) → kept in the goal file | documented |
| BRD-RULE-GOAL-07 | §10; §14 | Clients are chosen by goal, never by AML risk profile; one generic message for all clients with the same goal type; messages naming PEP, risk rating, suspicious transactions, enhanced monitoring or transaction reporting are refused — the aim is to never reveal that a client is monitored (tipping-off) | documented |
| BRD-RULE-GOAL-08 | §10 | Worked example: a draft AML-supervision circular (NHNN, 2026); a family with a study-abroad payment in Australia in March 2027 and 8 extra weeks → milestone 7/12/2026, level “Nhắc trên thẻ mục tiêu” (draft) | documented |

## DATA — data quality and storage (§11.3, §11.4)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-DATA-01 | §11.3 | Each asset carries a trust label: verified, from a statement, self-declared. Model-valued assets (property, private equity) show their share in the result | documented |
| BRD-RULE-DATA-02 | §11.3 | Stale valuation prices are flagged by the post-check | documented |
| BRD-RULE-DATA-03 | §11.3; §11.4 | Each run stores a hashed snapshot of prices, configuration and portfolio (config version id, price snapshot id), so a recompute gives the same numbers | documented |
| BRD-RULE-DATA-04 | §11.3 | News carries published, ingested and event-created timestamps; an item published after its ingestion is dropped | documented |
| BRD-RULE-DATA-05 | §11.4 | Batched writes with the log: one operation writes every table it touches and its log row in one batch; on error nothing is written | documented |
| BRD-RULE-DATA-06 | §11.4 | `audit_log` has database triggers that block UPDATE and DELETE; each row has `prev_hash` and SHA-256 `hash` | documented |
| BRD-RULE-DATA-07 | §11.4 | No double approval: `decisions.idem_key` and `application_runs.idem_key` are unique — approving twice yields one run | documented |
| BRD-RULE-DATA-08 | §11.4 | Readable identifiers, e.g. EV-2026-0007 (event), VW-0007-v1 (view v1), AR-0007-v1-1 (run), NW-0013 (news), GL-F01-02 (goal) | documented |
| BRD-RULE-DATA-09 | §11.4 | Partition by the barrier: the AI part reads only news, events, views and non-sensitive configuration; families, goals, family_impacts, goal_impacts, rm_notes, audit_log are outside its reach | documented |
| BRD-RULE-DATA-10 | §11.4 (moving to the bank) | Keep the entities and relations; move to PostgreSQL or the bank's standard DB; split frequently queried JSON fields into tables; encrypt client-data columns; put `audit_log` on WORM storage | documented |

## LC — state lifecycles (§11.4)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-LC-01 | §11.4 | View: DRAFTING → PENDING_CHALLENGE → PENDING_APPROVAL → APPROVED; an edit returns it to PENDING_CHALLENGE; side states AGENT_ERROR (format wrong after 2 retries), REWORK_REQUESTED (new version), REJECTED, WITHDRAWN, SUPERSEDED | documented |
| BRD-RULE-LC-02 | §11.4 | Application run: COMPUTING → POST_CHECKING → EFFECTIVE, or NEEDS_CIO_REVIEW when the post-check has a Critical finding (CIO makes it effective with a reason, or withdraws it), or FAILED on a computation error; later SUPERSEDED or WITHDRAWN. RMs see only EFFECTIVE, SUPERSEDED, WITHDRAWN | documented |
| BRD-RULE-LC-03 | §11.4 | Research: PENDING_RELEASE → RELEASED or REJECTED | documented |
| BRD-RULE-LC-04 | §11.4 | Inbox package (external_outputs): READY → PROCESSING → IMPORTED or REJECTED with error; an unsigned record is REJECTED when the key is set | documented |

## SEC — security, permissions, log (§13)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-SEC-01 | §13.1 | Only a verified sign-in token is trusted; roles come from an email mapping (bank target: SSO, least privilege by role and assigned families) | documented |
| BRD-RULE-SEC-02 | §13.1 | Every API checks the role before processing | documented |
| BRD-RULE-SEC-03 | §13.1 | Internal explanations for RMs are stamped “Nội bộ” | documented |
| BRD-RULE-SEC-04 | §13.1 | Separation of duties: research releaser ≠ uploader; newsletter approver ≠ author; two people for prompts, AI models, the factor model, alert thresholds and the restricted list. Compare by demo user id by default; `SOD_STRICT` compares verified emails | documented (Q-15 resolved by ADR-0016: the sentence and F14 apply) |
| BRD-RULE-SEC-05 | §13.1 table | Configuration owners: thresholds, return assumptions, factor model → CIO (two-person: no); white/restricted lists, forbidden phrases, data-sharing consent → Compliance (no); prompts, AI models → Admin (**yes**); news sources, price sources, ticker mapping → Admin (no) | documented (two-person per ADR-0016) |
| BRD-RULE-SEC-06 | §13.2 | Unreleased or not-yet-published research never reaches an agent | documented |
| BRD-RULE-SEC-07 | §13.2 | In inbox mode the external AI can only write to the inbox table; imports pass the same checks as live mode | documented |
| BRD-RULE-SEC-08 | §13.3 | Hash-chained log: SHA-256 by default; with `AUDIT_HMAC_KEY` set the hash is an HMAC and the chain may not be downgraded to plain SHA-256; production must anchor the chain head periodically on WORM storage | documented |
| BRD-RULE-SEC-09 | §13.3 | Stored end to end: source news → agent run (each step) → view → challenge → CIO decision → config and price snapshot → each family's result | documented |
| BRD-RULE-SEC-10 | §20 end | Protective keys and flags (`SOD_STRICT`, `EXTERNAL_HMAC_KEY`, `AUDIT_HMAC_KEY`, `ACCESS_AUD`) may be off in a demo so one operator can run the whole flow; a health endpoint lists which are off | documented |

## CONTENT — content that reaches clients (§14)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-CONTENT-01 | §14 | Three content flows: (1) general newsletter — market view, policy summaries, tied to no portfolio — CIO approves, Compliance approves the template; (2) family-specific update — impact by asset group and goal, **no ticker names, no action words** — CIO approves scenarios and template, RM pre-reviews severe cases; (3) action recommendation — per ticker, rebalancing, IPS change — certified specialist, RM discusses with the client | documented |
| BRD-RULE-CONTENT-02 | §14 | Every piece of client content carries: an “AI-assisted” label; the source of each news item and report; the responsible person's name; a timestamp; conflict-of-interest disclosure; “không phải khuyến nghị” in flows 1 and 2; a path to the RM or a complaints channel | documented |
| BRD-RULE-CONTENT-03 | §14 | “Exclusive” research means TCB's own analysis of public information, not early access: upload only after the official release time; no drafts and nothing obtained as a lender; disclose conflicts of interest when it concerns an organisation related to TCB or TCBS | documented |
| BRD-RULE-CONTENT-04 | §14 (legal table) | Label AI content sent to clients; no path around the CIO and RM gates (AI Law 134/2025/QH15) | documented |

## MEAS — measuring after go-live (§16)

| ID | Source | Rule | Doc status |
|---|---|---|---|
| BRD-RULE-MEAS-01 | §16.3 | Band coverage: share of realised moves inside P10–P90 per factor and horizon; accept 70–90 % (below: too narrow; above: too wide); at least 24 observations per horizon before concluding; measured after 1 week, 3 months, 12 months | documented |
| BRD-RULE-MEAS-02 | §16.3 | Direction hit rate, monthly | documented |
| BRD-RULE-MEAS-03 | §16.3 | Misses: important news that never became an event; events that did not reach exposed families — monthly, with causes | documented |
| BRD-RULE-MEAS-04 | §16.3 | AI quality: share of scenarios the CIO edits, critical findings, rewrites for format errors — weekly | documented |
| BRD-RULE-MEAS-05 | §16.3 | Rubber-stamping: CIO time before approving, share approved without edits — monthly | documented |
| BRD-RULE-MEAS-06 | §16.3 | Business effect: clients with versus without the tool (control group) — quarterly | documented |
| BRD-RULE-MEAS-07 | §16.3 | A fixed AI evaluation set (sample news + expected results) runs whenever a prompt or model changes | documented |
| BRD-RULE-MEAS-08 | §16.2 | Model validation: the 2022 back-test is illustrative (in-sample); the out-of-sample test 2/2024–8/2026 is the basis for Model Risk review; conclusion: use the model for VN-Index, but FX and the SJC spread must be core shocks chosen by the CIO, not inferred | documented |

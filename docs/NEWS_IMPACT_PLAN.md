# OneWealth — news-impact system and redesign: analysis and plan

Status: **plan**, 2026-10-15. Branch `redesign/news-impact` (worktree `../mr-finance-redesign`).
Inputs: the BRD *Đặc tả bộ agent tác động tin tức – Yêu cầu kinh doanh và nền tảng công nghệ*
(15/10/2026, @Bob; repo root, read in full: 20 sections, 31 tables, 5 diagrams), this codebase at
`8f66b77`, and screenshots of every current screen (desktop 1440 px, phone 390 px).

## 0. The one fact that frames everything

The BRD describes **a different implementation**: TypeScript, Hono on Cloudflare Workers, D1/SQLite
(28 tables), React + Recharts, LangGraph, ~80 endpoints, ~18 screens, 143–160 Vitest tests. Its
"Demo: Đã có" column and §7, §11, §12 refer to *that* system. It is not in this repository, not on this
machine, and nothing in our history touches it. So:

- the BRD is used as a **requirements source** only; every requirement below is mapped against
  *our* code, where almost all of the news-impact loop is **missing**;
- its technology choices (Hono, D1, React, LangGraph, Zod, decimal.js) are not requirements. We keep
  this repo's stack — Python, operonx graphs and services, SQLite, a no-build web UI — which already
  covers each role they play (§4).

## 1. The current system

**What it is.** A client-centric wealth demo. Five mock clients (and two spouses) whose holdings are
consolidated from three tiers of sources into one list (`consolidate_flow`, shared by every feature);
a dashboard; statement reading (AI or rules); a declaration chat (operonx-agents, AI or rules); an
adaptive risk test; 9 life-event simulations and 5 stress tests; an RM approval queue; and, since My's
OneWealth work, a specialist team, house views and an "advisory performance" page (mock data).

| Layer | Today | Size |
|---|---|---|
| Services | 9 operonx `http` services (one per graph) + one `asgi` app (static UI, plain reads); one job (`policy_sweep`, 07:00) and one eval | `app/main.py`, `app/web.py` |
| Domain | `src/wealth` (fixtures, store, valuation, money), one package per feature | ~5,000 lines Python |
| "Impact" | `alerts_flow`: 19 static factors (14 policies, 2 macro, 3 infrastructure) × 16 hand-written rules → one point estimate `exposure × sensitivity × probability` per hit | `src/impact` |
| Stress tests | 5 single-shock tests with fixed drawdowns per class (`stress_drawdown`) | `src/scenarios/_sim.py` (1,079 lines) |
| State | SQLite `data/state.db`: what clients add, results, the RM queue | `src/wealth/store.py` |
| UI | one page, vanilla JS, no build: `app.js` 1,386 lines (8 `render*` functions), `charts.js`, `app.css` | `web/` |
| Tests | 72, offline, ~19 s | `tests/` |

**Limitations that matter for the BRD** (each verified in code):

1. **No news at all.** "Headline News" is the static `data/factors.json` list; nothing is fetched,
   timestamped, deduplicated or grouped into events.
2. **No scenario engine.** Impact is one number per rule, with a hand-set probability; there are no
   factors, no correlations, no distribution, no horizons. Stress tests are a second, separate engine
   with their own fixed drawdowns. The BRD (BR-08, finding F03) requires **one** engine.
3. **No human control loop.** No CIO, Compliance or RM roles with actions; no approval states; no
   audit trail. The "Khách hàng / Nội bộ" switch only shows or hides tabs.
4. **No traceability.** A number on screen cannot be traced to a source, a scenario or an approval.
5. **UI.** Measured on the current screens (desktop): Headline News is 1,841 words over 3,626 px
   with no chart (7,410 px on a phone); Planning 1,073 words; every alert card repeats the same
   three formula rows; the overview's cash-flow chart is mostly empty space; pillar and tab labels
   mix English and Vietnamese and repeat each other ("Wealth View" → "Wealth view"). There is one
   chart vocabulary (bars) and no detail view: everything is expanded at once.
6. **Frontend structure.** One 1,386-line script with page logic, data shaping and HTML strings
   together; formatting and business rules (e.g. severity colours, goal status) are re-derived in
   the browser.

**What is good and stays:** consolidation with trust labels and family scope; the holding model
(class, sector, beta, bond duration, area, currency); the graph-per-feature structure and its tests;
the rule/AI fallback pattern (`MF_AI`); money in VND integers; the no-build UI; the validated chart
palette.

## 2. The BRD, organised

**Purpose.** Turn each important news event into money: expected VND gain/loss with a P10–P90 band
(and P5 for reference) for 1 week, 3 months and 12 months, for every position, loan and goal of every
Private family. "AI writes scenarios, the machine computes the numbers, people approve."

**Actors.** CIO (runs the CIO agent, edits and approves scenarios, owns the factor model); RM (sees
their families' post-checked results, enters goals, calls clients); Compliance (releases research,
owns white/restricted lists, owns the challenger and policy agents, traces); Admin (sources,
operations); certified specialist and client (later phases).

**The workflow** (BRD §5): fetch news every 10 min, gate it (white list, timestamps, restricted list)
→ CIO groups news into an event → CIO agent (4 analyst groups → bull/bear debate ≤ 2 rounds →
2–4 scenario branches with probabilities and core shocks → schema check, ≤ 2 retries) → challenger
agent (another model) files findings → CIO edits, answers findings, approves / returns / rejects /
withdraws → engine computes every family on a frozen snapshot → post-check rules → ranking; families
whose bad case (P10, 3 months) loses ≥ 5 % of net worth go to RM pre-review → RM sees the result.
A separate **goal branch** turns released regulation notes into dated preparation tasks for goals
with money going abroad.

**Business rules worth quoting** (they drive tests): 2–4 branches; probabilities 5–95 %, summing to
100 % ± 1.1; 1–5 core shocks per branch, factors from the catalogue, size S/M/L; rationale ≥ 20
characters; sources must belong to the event; priced-in multiplier 1 / 0.5 / 0; shock-size
uncertainty σ = 40 % of the shock; horizons 0.25 / 3 / 12 months with per-factor realisation
(table 9.2); RM pre-review when the 3-month bad case ≤ −5 % of net worth; goal deadline = first day of
the month money is needed − (extra prep weeks + 4); goal levels "contact now" (≤ 3 months and the
text is in force), "remind on goal card" (≤ 104 weeks or draft), "note"; messages mentioning PEP,
risk rating, suspicious transactions or monitoring are refused; research is released only by
someone other than its uploader, after its publication time; an approval is idempotent; the audit log
is append-only and hash-chained.

**Non-functional** (NFR-01…12): one event for all families ≤ 5 min; family page ≤ 2 s; news to inbox
≤ 10 min; AI failure must not stop computation or viewing; deterministic to the dong for the same
snapshot; exact money; Vietnamese; a "cách tính" (how computed) on every number; desktop and phone;
token budget per event; logs and alerts on feed, agent and audit-chain failures.

### 2.1 Ambiguities, gaps and risks (facts vs our recommendations)

| # | In the BRD | Problem | Our recommendation (not a BRD requirement) |
|---|---|---|---|
| A1 | Factor model "estimated from 55 months" | The covariance values are not in the document; we have no VN history series (VN-Index, foreign flows, SJC gap, VN rates) | Versioned factor-model file with **assumed** vols and correlations, every parameter labelled "Giả định", CIO-editable through config versions. Estimation script is a documented boundary (§7, blocker B1) |
| A2 | 20 mock families | We have 5 clients and 2 spouses | Run over our clients (family scope = household). Ranking and BR-13 work at any count |
| A3 | Roles via Cloudflare Access / SSO | No identity provider here | A demo identity switcher (CIO, RM, Compliance, Admin, client) whose user id is sent with each action; the server enforces role and separation of duties by that id. **Not security**; labelled as such |
| A4 | AI runs in a separate zone with its own DB, pushes signed results (§7.1) | One process here | Enforce the barrier in the graphs: agent ops take only news, event, research and factor catalogue as inputs; a test asserts no family data reaches an agent. The signed outbox (HMAC inbox) is phase-later |
| A5 | Market prices "real, by day" | Our market file is mock (2026-10-09); news will be real | Keep mock prices (the client data is mock anyway), label the price date on every result; a price provider is a boundary (B2) |
| A6 | BR-08: one engine for ranking, alerts, goals, explanation | Our alerts mix price moves (gold policy, market upgrade, rates) with cash costs (property tax, transfer tax, PIT relief) | Price-moving factors go through the scenario engine. Cash-cost rules are not price moves and stay as "Chi phí chính sách", outside the impact ranking. Stress tests become core-shock presets run by the same engine |
| A7 | Content to clients needs Legal (3 flows) | Our app has a client view | Client view shows only effective, post-checked results at asset-class level (flow 2: no tickers, no action words, "không phải khuyến nghị", AI label). Ticker-level detail is staff-only |
| A8 | CIO agent Opus, challenger Sonnet | One model configured (OpenRouter, Haiku) | Two env-configured models (`LLM_MODEL_CIO`, `LLM_MODEL_CHALLENGER`), refused if equal; `mock` mode (keyword scenarios) for tests and offline, as FR-307 |
| A9 | P10 is called "xấu" (bad) and drives the 5 % rule | Normal mixture; thin tails (F09) | Follow the BRD: P10 3-month drives pre-review, P5 shown as reference only |
| A10 | Exact decimal money (NFR-05) | The BRD itself computes scenarios in floats (F22) | Engine in floats, every VND result rounded to the dong at one place; balances stay integers |
| A11 | FR-801 CIO newsletter, BR-15 accuracy tracking | Need time to pass / distribution decisions | Optional, last |

## 3. Requirement → implementation traceability

Status in **our** code: ✗ missing · ◐ partial · ✓ exists. Phase refers to §6.

| Req | Requirement (short) | Ours today | Where it lands | Phase |
|---|---|---|---|---|
| BR-01 | 3 sources, labelled per item | ✗ | `src/news`: RSS fetch (international / domestic) + research upload (exclusive) | N1, N4 |
| BR-02 | White-listed public sources; published ≤ ingested | ✗ | `news.gates`: white list from config; future time > 10 min refused (F20) | N1 |
| BR-03 | Research enters only when released by someone else, after release time | ✗ | `src/research`: upload → release (SoD) → visible | N4 |
| BR-04 | Restricted-list mentions held for Compliance | ✗ | `news.gates.restricted`; event `blocked` until cleared | N1 |
| BR-05 | 2–4 scenarios with probability, core shocks, sources; AI gives no numbers | ✗ | `src/views`: CIO agent graph + schema checks; numbers only from the engine | N2 |
| BR-06 | Independent challenge before approval; critical findings answered | ✗ | challenger graph (other model); approval blocked until critical findings answered | N2 |
| BR-07 | CIO approves; nothing computed before | ✗ | `views.decide`; `apply` only from an APPROVED view | N2, N3 |
| BR-08 | VND per position and loan, 3 horizons × E, P5/P10/P50/P90; one engine | ✗ (point rules) | `src/engine` (pure) + `src/apply` | N0, N3 |
| BR-09 | ≥ 5 % NW 3-month bad case → RM pre-review | ✗ | `apply.flag`; RM "Hôm nay" queue | N3 |
| BR-10 | Regulation affecting goals abroad → right families, no AML data | ✗ | `src/procedural` goal branch | N4 |
| BR-11 | AI never reads client data | ✗ (n/a) | graph inputs + barrier test | N2 |
| BR-12 | Every number traceable; immutable log | ✗ | `src/control.audit` hash chain; trace endpoint per family number | N3 |
| BR-13 | CIO sees exposure of all clients by factor | ✗ | `apply` aggregate + heat map | N3 |
| BR-14 | CIO withdraws a view; RM sees "Đã thu hồi" | ✗ | view/run state machine | N3 |
| BR-15 | Accuracy over time | ✗ | optional: realised vs band once prices move | N5 (opt.) |
| FR-101…105 | RSS every 10 min, classify, inbox, gates, restricted | ✗ | `ingest` Job `every="10m"`; inbox screen | N1 |
| FR-201…204 | Research and regulation notes, release | ✗ | `src/research` | N4 |
| FR-301…307 | CIO agent graph, impacts −3..+3, challenger, CIO edit, preview, policy agent, 3 run modes | ✗ | `src/views` (live + mock; policy agent optional) | N2 |
| FR-401…406 | Snapshot + hash, per-family result, ranking, goal impact, recompute, "cách tính" trace | ✗ | `src/apply` | N3 |
| FR-501…503 | Post-check rules; RM sees only effective; pre-review flag | ✗ | `apply.postcheck` | N3 |
| FR-601…604 | Goal outflow purpose, matching, levels, forbidden wording | ◐ goals exist (planning) without outflow fields | `src/procedural` + goal fields | N4 |
| FR-701…704 | Versioned config with two-person rule, hash-chained log, agent catalogue, run trace | ✗ (operonx traces exist for runs) | `src/control`; agent run trace reuses operonx traces | N3, N5 |
| FR-801 | CIO newsletter | ✗ | optional | N5 (opt.) |
| NFR-01/02/04/05/11 | Speed, determinism, money, "cách tính", phone | ◐ | tests + UI acceptance (§5) | all |

Out of scope (BRD §3): order placement or any automatic transaction; ticker-level advice sent to
clients; connecting outside data (Open API) — the existing mock tiers stay as they are; real-estate
transaction pricing.

## 4. Target architecture

Same stack, clear boundaries. Each box is a package with pure functions and one or more operonx graphs;
the arrows are the only allowed data flows.

```text
 news (fetch, gate, classify) ─► events ─► views: CIO agent ─► challenger ─► CIO decision
     ▲ RSS, research release          (inputs: news, research, factor catalogue — never client data)
                                                                  │ APPROVED
 wealth/consolidate (holdings) ──────────────────────────────►  apply: snapshot → engine → post-check
                                                                  │      → ranking, RM flag, goals
 control: config versions, roles + SoD, audit hash chain  ◄── every write
 web: role workspaces, reading effective results through stable JSON contracts
```

| Package | Responsibility | Notes |
|---|---|---|
| `src/engine` (new) | factor catalogue (15 factors, S/M/L, realisation by horizon), regime covariance (normal, stressed), conditional expectation, holding → factor loadings, mixture → mean, P5/P10/P50/P90 per horizon; contributions by factor, class, position | **pure, deterministic, no I/O**; the only place numbers come from |
| `src/news` (new) | sources config, RSS fetch, normalise, dedupe, timestamps, white/restricted gates, rule classification (intl/domestic, relevance, event type hint) | Job `ingest` every 10 min |
| `src/events` (new) | group news into an event; restricted hold | CIO action |
| `src/views` (new) | CIO agent graph (4 analysts in parallel → debate → synthesis → schema check with retries), challenger, decisions state machine, scenario edits | live (two models) or mock |
| `src/apply` (new) | application run: freeze holdings + prices + config (hash), run engine for every client, post-check, ranking, RM flag, goal impact, recompute, withdraw | only from APPROVED views |
| `src/research`, `src/procedural` (new) | research and regulation notes with release; goal branch | N4 |
| `src/control` (new) | audit log (SQLite trigger blocks UPDATE/DELETE, SHA-256 chain, verify), config versions (propose/confirm), roles and SoD | every write goes through it |
| `src/impact` (changed) | keeps cash-cost policy rules only, shown as "Chi phí chính sách"; price-moving factors retire to engine presets | A6 |
| `src/scenarios` (changed, N5) | stress tests become core-shock presets on the engine | one engine |

**Persistence.** The existing `data/state.db`, new tables with indexed columns plus a JSON `data`
column (the BRD's own pattern, and ours): `news_items`, `events`, `views`, `challenges`, `decisions`,
`application_runs`, `run_snapshots`, `family_impacts`, `goal_impacts`, `config_versions`,
`audit_log`, `agent_runs`. Readable ids (`EV-2026-0007`, `VW-0007-v1`, `AR-0007-v1-1`, `NW-0013`).

**API contracts** (JSON, stable, consumed by the UI): graphs stay `http` services; plain reads stay in
the asgi app.

| Method | Path | Graph / read |
|---|---|---|
| GET | `/api/news/inbox` | read (filters: source, kind, since) |
| POST | `/api/events` | `event_flow` (group news) |
| POST | `/api/events/run-agent` | `cio_agent_flow` → view DRAFT → challenger |
| GET | `/api/views/{id}` | read (view, findings, history) |
| POST | `/api/views/decide` | `decide_flow` (edit, answer, approve / return / reject / withdraw) |
| GET | `/api/runs`, `/api/runs/{id}` | read (ranking, exposure by factor) |
| GET | `/api/families/{id}/impact` | read (effective results, bands, contributions) |
| GET | `/api/trace/{run}/{family}` | read (number → scenario → decision → news) |
| GET | `/api/audit/verify` | read |
Existing endpoints are unchanged.

**Frontend.** No framework is needed (the UI is read-mostly with forms; React would add a build step
for no verified need). The single script splits into ES modules: `web/core/` (api client, store,
router, format, components: card, stat, table, badge, empty / error / loading states, detail drawer),
`web/charts/` (bar, line, band/fan, heat map, timeline — one tooltip and legend model),
`web/pages/` (one module per screen). Business rules move server-side: the UI receives severity,
status and labels already decided.

## 5. Information architecture and screen redesign

**Design language.** The BRD's diagrams already have one, and we adopt it: white surfaces, thin
neutral borders, blue = AI, orange = a human checkpoint, grey = client data. Money: green gain, red
loss, grey neutral, hatched or dashed = uncertain / modelled, "—" = unavailable. One type scale,
8 px spacing grid, tabular numbers, light and dark from the same tokens.

**Navigation by role** (replaces the five English pillars and their duplicate tabs):

| Role | Pages |
|---|---|
| Khách hàng | Tổng quan · Tài sản · Mục tiêu & kịch bản · Tin tác động · Chuyên gia |
| RM | Hôm nay (pre-review cases, goal tasks, approval queue) · Khách hàng (the family pages, ticker detail, trace) · Hiệu quả tư vấn |
| CIO | Hộp tin · Sự kiện & nhận định · Phơi nhiễm toàn bộ khách · Lần áp dụng · Mô hình |
| Tuân thủ | Nghiên cứu · Danh sách · Nhật ký |

**Key screens.**

- **Tin tác động (family).** Headline: the effective 3-month expected impact in VND and % of net worth
  with its P10–P90 band. A **fan chart** (expected, P10–P90, P5 dashed) across 1 week / 3 months / 12
  months. Contributions as a diverging bar by factor and by asset class. Below, the event timeline:
  each approved event a row with direction, size and "cách tính" opening the trace drawer
  (number → positions → scenario branches → CIO decision → news sources). Withdrawn and superseded runs
  labelled. Policy cash costs as a short separate list. Empty state when no event is effective.
- **Hộp tin (CIO).** A dense, filterable list (source, kind, relevance, time), multi-select to group into
  an event; blocked items flagged. A small sparkline of items per hour per source shows feed health.
- **Nhận định (CIO).** The scenario tree: branches as stacked probability bar, each with core shocks
  (factor, direction, S/M/L) and sources; impact rows −3..+3 as a compact matrix; challenger findings by
  severity with answer boxes; the lifecycle as a stepper (Draft → Challenge → Approval → Approved).
  A market-level preview per branch (FR-305) before approving.
- **Phơi nhiễm toàn bộ khách (CIO, BR-13).** Heat map clients × factors (VND or % NW), ranked list with
  the pre-review flag.
- **Tổng quan (client).** Net worth, change and trust mix in one band; allocation; the cash-flow chart
  redrawn so empty months take little space; the top effective news impacts. Every secondary block
  collapsible.

**Acceptance for the UI** (measured with the same script as the baseline): news page word count
≤ 40 % of today's 1,841 and phone height ≤ 50 % of 7,410 px; no horizontal scroll at 390 px; every chart
has a legend or a direct label, a tooltip on every mark and a table view; light and dark; loading, error,
empty and partial states on every page; screenshots desktop and phone for every screen.

## 6. Sequence

Each phase is one unit of work with its gate; essential first.

| # | Phase | Delivers | Gate |
|---|---|---|---|
| N0 | **Engine** | `src/engine`: 15-factor catalogue (BRD 9.2 shock sizes and realisation; assumed vols and correlations, labelled), stressed regime as the BRD builds it, conditional propagation, loadings for every holding class (9.3), mixture percentiles; contributions | unit tests: determinism; bands widen with horizon and are ordered; priced-in multipliers; covariance symmetric and positive definite (refuse otherwise); the 9.4 gold example's structure; loans move the right way |
| N1 | **News** | sources config (VnExpress, VnEconomy, Fed, …), RSS fetch, gates, classify; `ingest` Job every 10 min; `/api/news/inbox` | tests on fixtures (no network): white list, future timestamps, duplicates, restricted hold; one live fetch smoke |
| N2 | **Views and agents** | events; CIO agent graph (live / mock) + schema checks + retries; challenger (other model); decisions state machine; barrier test | tests: probability sum, factor catalogue, sources ∈ event, retries then AGENT_ERROR, edit → re-challenge, critical finding blocks approval, idempotent approval, no client data in agent inputs |
| N3 | **Apply, control** | application runs with snapshot hash, post-check, ranking, RM flag, BR-13 aggregate, withdraw / supersede / recompute, audit chain + verify, trace endpoint | tests: recompute equals to the dong; RM sees only effective; −5 % rule; audit tamper detected; withdraw labels |
| U1 | **Design system and shell** | tokens, components, charts, role navigation, ES-module split; existing pages ported unchanged in behaviour | the 72 existing tests; screenshots of every page desktop + phone |
| U2 | **Redesigned screens** | client: Tổng quan, Tài sản, Mục tiêu, Tin tác động (fan chart, contributions, trace); RM: Hôm nay; CIO: Hộp tin, Nhận định, Phơi nhiễm, Lần áp dụng | UI acceptance (§5) |
| N4 | **Research and goal branch** | research upload / release (SoD), regulation notes, goal outflow fields, matching, levels, forbidden wording | tests: SoD, release time, name inference only makes an RM task ("Nhật Minh"), draft never "contact now", PEP wording refused |
| N5 | Optional | stress tests on the engine; agent catalogue; CIO newsletter; accuracy tracking; HMAC inbox | — |

Order: N0 first (everything shows its numbers), then N1–N3 (the loop end to end on mock agents), then
U1–U2 (screens on real contracts), then N4, then N5 if time allows. The live demo on :8030 runs `main`
and is not touched until a phase merges; each merge is followed by a restart of the demo.

## 7. Blockers and boundaries (left explicit, not faked)

| # | Blocker | Boundary left in the code |
|---|---|---|
| B1 | No historical VN series to estimate the factor model | parameters marked `assumed`, a versioned config the CIO can edit; `scripts/estimate_factors.py` boundary documented, not written |
| B2 | No licensed price feed | mock prices with their date on every result; `PriceSource` interface with the mock as its only implementation |
| B3 | No SSO | demo identity switcher; the server checks role and SoD by user id; marked "not security" |
| B4 | Model budget and the CIO / challenger model choice | env-configured models; live runs only on demand; token cap per run; mock mode by default in tests |
| B5 | Legal sign-off on client content (3 flows) | client view at asset-class level with disclaimers; nothing is sent to clients |
| B6 | Separate AI zone and signed inbox | barrier enforced in graphs and tests; HMAC inbox optional (N5) |

## 8. Migration and compatibility

- Existing endpoints, graphs, the job and the eval keep their contracts; new tables are created on
  demand, so an old `state.db` works and `reset` clears the new tables too.
- "Headline News" is replaced by "Tin tác động"; the old static factors remain readable until N5
  retires the price-moving ones (A6).
- Mock data stays generated by `scripts/make_*.py` (D1 of docs/PLAN.md); the factor model file is
  generated the same way.
- The UI keeps working with pip and uv and needs no build.

## 9. Status (2026-10-15)

| Phase | State | Commit | Evidence |
|---|---|---|---|
| N0 engine | done | 325fddf | 29 tests; recompute equals to the dong; the stressed matrix needs the BRD's eigenvalue repair (smallest eigenvalue before −0.17, largest correlation change 0.10) — kept in the model and shown on the Mô hình page |
| N1 news | done | 09f2cdc | 11 public feeds checked live (Báo Đầu tư, Nhân Dân, VTV gave no items that day and stay out); first fetch 2 s, 361 items kept, 34 duplicates dropped; 17 tests on written feeds |
| N2 views and agents | done | 7240ac4 | live run with two models (Sonnet 5.5 CIO, Haiku 5.5 challenger): CIO 26 s over 7 nodes, challenger 13 s, 8 findings of which 3 critical; token caps set from those runs; 23 tests incl. the barrier (no client name, account or balance in any prompt) |
| N3 apply and control | done | af313a0 | approve → run for every family in 0.44 s (5 families); verify recomputes from the snapshot to the dong; audit chain in the same transaction as every write; 13 tests |
| U1 + U2 screens | done | 5bac1fd | news page 1,841 → 257 words, phone 7,686 → 1,909 px (targets ≤ 736 and ≤ 3,705); 84 screenshots (21 routes × desktop/phone × light/dark) without horizontal scroll or console error; 6 click-through flows |
| N4 research and goal branch | done | b1ca845 | the BRD §10 example reproduced (milestone 2026-12-07, “Nhắc trên thẻ mục tiêu”); name traps (Mỹ Linh, Nhật Minh, Minh Đức) not matched; 15 tests |
| N5 optional | not started | — | stress tests on the engine, agent catalogue, CIO newsletter, accuracy tracking, HMAC inbox |

**Correction (2026-10-15, documentation audit):** N3 did not build FR-404 (goal impact per run: funding
before/after, Đạt / Theo dõi / Thiếu), and the restricted-list release did not check the Compliance role (DEF-03).
Both were fixed the same day; FR-404 is built on our definition (`src/apply/goals.py`, Q-11). Status of every requirement now lives in
`docs/brd/requirements/requirements_traceability.md`.

Deviations from §4, said plainly:

- Packages: `src/events`, `src/views`, `src/apply`, `src/control`, `src/research`, `src/procedural` as planned; the CIO agent's
  retry loop is inside the synthesis op (each attempt is its own recorded node), not a graph back-edge.
- The client view of a run shows the event's type ("Vàng"), not the headline: a headline can name a company (flow 2).
- `src/impact` (cash-cost policy rules) and the stress tests are unchanged; moving price-moving factors and the stress tests
  onto the engine is N5 (A6).
- Live agents need `LLM_MODEL_CIO` and `LLM_MODEL_CHALLENGER` (two different models) in `.env`; without them every run is
  the labelled mock, never a silent fallback.

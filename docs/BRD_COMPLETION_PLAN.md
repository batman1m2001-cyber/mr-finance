# OneWealth — Finishing the BRD's original features: audit and plan

The owner asked (2026-10-16) to finish the original features of the BRD “at all cost”. The BRD has two parts:
the news-impact agent system it specifies (§1–§20) and the UI/UX of the redesign kit. The UI/UX part is done
([UI_REDESIGN_REPORT.md](UI_REDESIGN_REPORT.md)). This plan closes the first part.

Sources re-read for this audit:
- the traceability matrix;
- the BRD extracts (`business_requirements.md`, `functional_requirements.md`, `non_functional_requirements.md`,
  `business_rules.md`);
- `open_questions.md`;
- the feature files;
- the code (`src/`, `app/main.py`);
- a probe of every public market-data source, run on 2026-10-16 (§3).

## 1. Where the BRD part stands

There are 165 BRD rows in the matrix:

| Status | Rows |
|---|---|
| Verified | 108 |
| Out of scope (rules of the author's stack) | 15 |
| Not applicable | 2 |
| Open | 40 |

The 40 open rows break down into partial (19), unverified (9), blocked (5), planned (4) and not built (3).

A further 17 rows are marked `out_of_scope_demo`. Six of them become buildable with what this plan adds, so they
are brought in:
- ZONE-01, ZONE-06, SEC-07 (with the inbox mode);
- SEC-01 (sign-in tokens);
- MEAS-05 (rubber-stamping);
- MEAS-08 (model validation on history).

That makes **46 rows** to close.

The open rows, grouped by what closes them:

| Theme | Rows | What is missing |
|---|---|---|
| A. Market history | BR-15, KPI-03, KPI-04, MEAS-01, MEAS-02, ENG-11, MEAS-08 | No price history. Every factor-model parameter is assumed (Q-22), and no forecast can be scored |
| B. Configuration | FR-701, SEC-04, SEC-05, AI-02, NFR-06, MEAS-07 | Not yet configuration: return assumptions, forbidden phrases, consent, price sources, ticker mapping, prompts, models. There is no eval set gating a prompt or model change |
| C. Identity and access | SEC-01, ROLE-02, SEC-02, ROLE-04 | The UI sends a user id that the server trusts. An RM sees every family. Reads are unchecked. There is no admin screen |
| D. Run modes and the AI zone | AI-13, FR-307, ZONE-01, ZONE-02, ZONE-06, LC-04, SEC-07 | Live runs block the request. There is no job queue, no inbox mode, no separate AI zone and no signed import |
| E. Observability | NFR-12, NFR-03 | Failures are visible on demand; nothing alerts. An AI outage leaving computation and reads working is not tested |
| F. Newsletter and content | FR-801, CONTENT-01, CONTENT-02, CONTENT-03, SEC-04 (newsletter part) | No newsletter (flow 1). Conflict-of-interest disclosure is free text and not shown to clients |
| G. Policy agent | FR-306, AI-01 | The third LLM task is not built. “Radar” is undefined (Q-09) |
| H. Rules not enforced or not tested | AI-05, FR-101, WF-01, WF-03, WF-04, NFR-02, WF-09, FR-603, SEC-03, BR-08, NFR-01, NFR-11, MEAS-03, MEAS-05 | AI-05 is not enforced after the answer. Schedules are not asserted. Two pages are not browser-tested. There is no VND sum per goal, no 6,500-family run and no client-level “cách tính” (Q-14). The misses and rubber-stamping reports are not built |

These rows **cannot be finished inside a demo**, and the plan says so rather than faking them:
- NFR-03's 99.5 % uptime, NFR-07's encryption at rest, secret store and penetration test, and NFR-08's hosting in
  Vietnam and provider contract are deployment matters. NFR-03 and NFR-07 get the parts the code can carry:
  the AI-outage test and the prompt-injection test. NFR-08 stays as the owner decided in ADR-0018.
- KPI-02 (Q-07), KPI-05, KPI-06 and MEAS-06 are pilot measurements. ROLE-05 and WF-08 are a later phase in the
  BRD itself. DATA-10 is bank migration guidance.

## 2. Decisions

| # | Decision | Why |
|---|---|---|
| F-D1 | **Real market data feeds history, estimation and scoring. The demo families keep the mock price snapshot** (ADR-0005). Re-basing the portfolios is a separate owner choice | Real prices would change every demo number (mock FPT 128,000 vs real 58,000) with no requirement asking for it |
| F-D2 | **Each outside source is one operonx op in its own scheduled job, behind an adapter** with an ordered fallback, chosen by the new `price_sources` configuration (owner Admin, BRD §13.1). Every stored point records source, URL and fetch time. The suite never touches the network: adapters are tested on recorded responses, plus one live smoke script | The sources are unofficial and can change without notice |
| F-D3 | **Factors without a free series stay “Giả định”**: RE_SPREAD, FIN_SPREAD, VN_HOUSE. VN_RATE uses the HNX 3-month government spot rate as a labelled **proxy**, because the SBV rate portal does not accept connections from this server | ENG-11 asks for per-factor provenance, which is exactly this. Nothing is invented |
| F-D4 | **Estimation follows BRD §9.2**: 55 monthly observations and 20 % shrinkage of the correlations toward zero (the identity). The estimated model is **proposed as a new `factor_model` version and approved by a second CIO**, through the same two-person flow as any change | ENG-11, AI-02 and ADR-0016. The model change is itself audited |
| F-D5 | Accuracy is measured two ways. First, the model's bands against history: for each month, is the realised move inside P10–P90 for each factor and horizon? This needs ≥ 24 observations, which history already gives. Second, each approved view's own bands as their horizons pass. Out-of-sample means estimating on data up to 1/2024 and testing 2/2024–8/2026, as MEAS-08 names | BR-15, MEAS-01, MEAS-02 and MEAS-08, without waiting months for views to mature |
| F-D6 | **Sign-in issues an HMAC-signed token**; every API takes the user from the token and ignores any `by` in the body. Users carry emails, and roles come from an email mapping. The demo keeps one-click demo accounts, labelled as demo-only, on the sign-in page; the bank swaps the issuer for SSO | SEC-01's mechanism is real; the public demo stays usable |
| F-D7 | **The AI zone is a second process** with its own SQLite file, holding only public news, released research and the approved catalogues (ZONE-01, ZONE-06). It reaches TCB through one write-only inbox endpoint that returns an id and no data. Packages are signed with HMAC-SHA256, and a 10-minute import job passes them through the same checks as live mode (ZONE-02, LC-04, SEC-07). Live mode runs as a background job, and the page follows its status (AI-13) | The BRD's architecture, built small |
| F-D8 | **“Radar chính sách” (Q-09) is our interpretation**: the tracked policy items with their status history (draft → consultation → passed or dropped), what changed since the last look, and the agent's quoted summary of each verified document. It is labelled “đề xuất” until the owner defines it | Resolve rather than defer; the label keeps it honest |
| F-D9 | **Q-14: the client gets “cách tính” at asset-class level**: the formula, factor moves and the class sums, with no holding names. Staff keep the full trace | NFR-11 and flow 2 together |
| F-D11 | **SQLite is the only place the app reads data from at request time**: the outside sources through their jobs (F1), the customers and staff from the `people` tables seeded from the JSON files | Owner's re-architecture, 2026-10-16 |
| F-D10 | Prompts and models become configuration (owner Admin, two people). A proposed change **runs the fixed eval set first** and shows its result on the proposal. Approval is refused when it fails | AI-02 and MEAS-07 |

## 3. Market data: what was found (probed 2026-10-16)

| Factor / data | Source (primary → fallback) | History |
|---|---|---|
| VNINDEX, stocks, ETFs | VNDirect `dchart-api` → Vietcap OHLC chart | daily since 2020 |
| USDVND | Vietcombank rate by date (`/api/exchangerates?date=`) → MSN | daily since 2020 |
| GOLD (world), BRENT, GLOBAL_EQ (ACWI), US10Y (TNX) | MSN Finance chart API (the anonymous key from its public config) → FRED, if `FRED_API_KEY` is set | daily since 2020 |
| DXY | computed from six MSN FX series with the published ICE formula | daily since 2020 |
| BTC | Binance klines | daily since 2017 |
| SJC price → SJC_GAP | PNJ gold history API (SJC bars) → giavang.org page | daily since 2020 |
| VN_GOV | HNX government yield curve by date → worldgovernmentbonds.com 10-year | daily; WGB since 2016 |
| FOREIGN_FLOW | cafef foreign trading history (HOSE, net value) | daily |
| VN_RATE | HNX 3-month spot (**proxy**; SBV portal closed to this server) | daily |
| RE_SPREAD, FIN_SPREAD, VN_HOUSE | none free (FiinPro or VBMA are paid) | stay assumed |

Blocked or unusable from here:
- SJC's own site and TCBS sit behind Cloudflare.
- Yahoo Finance answers 429.
- Stooq needs a captcha.
- FRED's keyless CSV times out.
- SBV's rate portal has port 443 closed to this server.

## 4. Phases

There is one branch and one PR per phase. Each phase updates the BRD docs (feature file, matrix, changelog) and
passes the suite and the doc checker. Screens get desktop and phone screenshots.

### F1 — The data layer (theme A, part; owner's re-architecture, 2026-10-16)

The owner asked for one architecture for data:
- every outside source is fetched on its own schedule and kept in SQLite;
- the people (customers with their personal information, and staff of every role) are in SQLite too.

The app reads SQLite, never the outside source or a JSON file, at request time.

**People** (`src/people/`). Tables:
- `people`: id, kind (staff or client), role, name, email, title, assigned RM, and the record;
- `client_sources`: what each mock bank, broker, fund or housing system holds for a customer.

The JSON files under `data/clients/` and a new `data/people/staff.json` become **seed files**. They are loaded
into an empty database and again on demo reset, and are never read at request time. `wealth.fixtures`
(`client`, `client_ids`, `summary`) and `control.roles` (`user`, `require`, the staff list) read the tables.
Three RMs (`rm01`–`rm03`) and each customer's assigned RM are added now.

**Sign-in** (pulled forward from F5 by the owner, 2026-10-16: “do the authen login”; ADR-0020). Everyone who acts
signs in with their own account and sees only their role's pages and the families they may see; the role
switcher is gone. **Done** in PR “F1 part 1: the people table and sign-in”.

**Outside sources** (`src/market/`, with the news kept in `src/news/`):
- one operonx op per data type: `equity_bars`, `fx_rates`, `world_series`, `crypto_bars`, `sjc_gold`,
  `gov_yields`, `foreign_flow`;
- each in its own graph and `Job`, with a cadence chosen from the source's rate limit and when its data changes:

| Job | Source (fallback) | Cadence | Why |
|---|---|---|---|
| `news_ingest` (exists) | 8 white-listed RSS feeds | every 10 min | BRD FR-101 |
| `market_equity` | VNDirect (Vietcap) | daily 15:45 | HOSE closes at 15:00; daily bars |
| `market_flows` | cafef | daily 16:00 | end-of-day foreign trading |
| `market_yields` | HNX curve (worldgovernmentbonds) | daily 17:30 | the curve is published at day end |
| `market_fx` | Vietcombank (MSN) | hourly | VCB asks for at most one request per 5 min |
| `market_world` | MSN (FRED, with a key) | hourly | world markets trade around the clock; ~12 requests a run |
| `market_crypto` | Binance | hourly | far inside Binance's public limit |
| `market_gold` | PNJ (giavang.org) | hourly | SJC prices move during the day |

Also in this phase:
- Every run of every source is recorded: `source_runs` holds source, started, finished, points, error.
- A source registry shows each job's cadence, last success and last error. F7 alerts on it.
- Stored data: `market_series` (series, date, value, source, url, fetched_at). An hourly run updates the day's
  point.
- `market_backfill`: an on-demand job (`operonx run market_backfill`) loading history from 2020-01. Sources that
  answer by date are sampled weekly, the rest daily.
- `factor_series` turns the stored series into the 15 factors' moves in their units (pct, bp, pp, sd), with each
  factor's provenance label.
- New config kinds `price_sources` and `ticker_map` (owner Admin).
- A read API `/api/market` and a staff “Dữ liệu thị trường” view: coverage, last point, source, cadence and
  failures.
- Tests on synthetic responses in each source's format, plus `scripts/market_smoke.py` against the live
  sources.

### F2 — Estimate the model and validate it (A)

- Estimate volatilities and correlations from 55 months with 20 % shrinkage, for the factors that have data.
  The rest keep their assumed values with “Giả định”.
- Propose the result as a `factor_model` version (CIO), approved by `cio2`.
- Validate out of sample (estimate to 1/2024, test 2/2024–8/2026) and write it up for Model Risk (MEAS-08).
- Enforce AI-05 after the answer: a stress scenario without VNINDEX and RE_SPREAD among its core shocks is
  refused, in live, inbox and mock modes alike.

### F3 — Accuracy over time and the measurement reports (A, H)

- FEAT-18: for every factor and horizon, band coverage and direction hit rate, from history and from each
  approved view. Include the “≥ 24 observations” rule and the 70–90 % acceptance band.
- A CIO “Độ chính xác” page, and a daily job that scores views whose horizon has passed.
- Reports:
  - MEAS-03, monthly misses with causes;
  - MEAS-05, rubber-stamping: CIO time before approving, share approved without edits;
  - KPI-01 and WF-09, news-to-RM time end to end;
  - NFR-02, agent run durations.

### F4 — Configuration completes (B)

- New kinds: `return_assumptions` (CIO), `forbidden_phrases` and `consent` (Compliance), `prompts` and `models`
  (Admin, two-person).
- The agents read their prompt and model from the active version, and the prompt version recorded on each run is
  that config version.
- The fixed eval set (sample news plus expected results) runs on every prompt or model proposal, and its result
  gates approval (MEAS-07).
- The content guard reads the forbidden phrases from configuration.
- New asset classes and agents can be declared in configuration where the engine allows it (NFR-06). Whatever
  stays code says so in the feature file.

### F5 — Identity and access (C)

- Done in F1 part 1 (ADR-0020): sign-in tokens (F-D6), accounts by e-mail, three RMs with assigned families, and
  the checks on reads and writes.
- Left: the RM-to-family assignment as configuration; a test that walks every served route as every role; a
  refused `POST` answering 403 instead of 500 (an operonx status mapping).
- An admin screen with configuration by kind, system status (feeds, agents, jobs, audit-chain check), data
  loading (market backfill) and users.

### F6 — Background runs, the AI zone and inbox mode (D)

- A job queue for live agent runs, with status on the event page (AI-13).
- The AI-zone process with its own database and write-only signed push (F-D7).
- The inbox table with its lifecycle (READY → PROCESSING → IMPORTED or REJECTED with the error), and a 10-minute
  import through the same checks.
- Mode switch: live, inbox or mock (FR-307).

### F7 — Observability and alerts (E)

- A central structured log.
- An `alerts` table, raised on:
  - a feed failure (news or market);
  - an agent failure;
  - a failed audit-chain check (a scheduled job);
  - a failed inbox import.
- Alerts appear in the staff bell and on the admin screen. Acknowledging one is audited.
- A test that kills the AI provider and checks the engine, runs and reads still work (NFR-03).

### F8 — Newsletter and content rules (F)

- FR-801: the CIO drafts a newsletter from approved views (template, or the CIO agent under the content guard).
- Default same-time distribution. Earlier Private access needs a justification that Compliance sees.
- Compliance approves, and the approver must not be the author. Preview only; nothing is sent.
- Conflict of interest becomes a structured field on research and newsletters, shown on client content
  (CONTENT-02, CONTENT-03).

### F9 — The policy agent (G)

- FR-306: summarises source-verified policy documents and quotes their articles exactly (each quote is checked
  against the document text). It never reads a portfolio.
- Mock and live modes.
- The radar (F-D8).
- Owner Compliance. The fourth LLM task, internal explanation, is already a template; recorded as such (AI-01).

### F10 — The remaining rules and verification (H), then the report

- BR-08: VND impact per goal (Q-03 recorded).
- NFR-01: a timed run over 6,500 synthetic families, plus family-page timing.
- Schedule tests (FR-101, WF-01, NFR-02).
- WF-03 and WF-04 tests.
- Browser tests for FR-603 and SEC-03.
- Client-level “cách tính” (F-D9).
- Doc sweep and matrix to final, then `docs/BRD_COMPLETION_REPORT.md` with every row's status and evidence.

## 5. What the owner may be asked

Nothing blocks the plan. Optional:
- **A FRED API key** in `.env` as `FRED_API_KEY` (free, from fredaccount.stlouisfed.org): an official fallback for
  the US series.
- **A paid data source** for credit spreads and house prices. Without one those three factors stay assumed,
  which the BRD allows when labelled.

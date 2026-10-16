# API reference

Every endpoint the product serves on port 8030 (2026-10-15). Writes are operonx services: the JSON body fills the
graph's parameters by name, the reply is the graph's outputs; an unknown field or a missing required one is a 400;
a raise in the graph's first op is a 500 with the run's trace id; a failed op shows as `"$errors"` in the reply.
Source of truth: [`app/main.py`](../../../app/main.py) (services) and [`app/web.py`](../../../app/web.py) (reads).

**Security note.** Writes of the news-impact system take a demo user id (`by`) and check its role on the server
(FEAT-12). Reads take no identity: `role=` is a query parameter the caller chooses (default `client` where it
matters), and the trace read is staff-only by the UI alone. This is the demo's role switcher, not access control
([ADR-0006](../decisions/ADR-0006-the-role-switcher-is-not-security.md)).

## Writes (POST, operonx services)

| Path | Service → graph | Body | Role checked | Feature |
|---|---|---|---|---|
| `/api/dashboard` | dashboard → `dashboard_flow` | `client_id, scope?, months?` | — | FEAT-21 |
| `/api/flows` | flows → `flows_flow` | `client_id, scope?, month? (YYYY-MM)` | — | FEAT-29 |
| `/api/feed` | feed → `feed_flow` | `client_id, scope?, role? (client\|rm)` | — | FEAT-31 (each item has a stable `key`, FEAT-33) |
| `/api/overview` | overview → `overview_flow` | `client_id, scope?, role? (client\|rm), goals? (ids followed)` | — (client: event types, classes for news) | FEAT-30 (R4) |
| `/api/search` | search → `search_flow` | `q, role, client_id?, scope?` | role decides the kinds; the client sees type labels only | FEAT-34 |
| `/api/copilot` | copilot → `copilot_flow` | `question, role, client_id?, scope?, route?, confirm?, goals?` | per tool (and the wrapped graph's own check) | FEAT-32; an ok answer has `focus` (FEAT-33), `as_of`, `answered_at`, `sources`, `card`; every call is an audit row (`audit_seq`) |
| `/api/config/propose` | config_propose → `config_propose_flow` | `kind, data, by, note?` | the kind's owner role | FEAT-14 |
| `/api/config/decide` | config_decide → `config_decide_flow` | `version_id, action (approve\|reject), by, note?` | owner role; ≠ proposer for two-person kinds | FEAT-14 |
| `/api/statement` | statement → `statement_flow` | `client_id, filename, content` (base64) | — | FEAT-22 |
| `/api/declare` | declare → `declare_flow` | `client_id, message, session_id` | — | FEAT-23 |
| `/api/risk` | risk → `risk_flow` | `client_id, answers` | — | FEAT-24 |
| `/api/alerts` | alerts → `alerts_flow` | `client_id, scope?` | — | FEAT-25 |
| `/api/scenario` | scenario → `scenario_flow` | `client_id, scenario, params?, scope?` | — | FEAT-26 |
| `/api/goals` | goals → `goals_flow` | `client_id, scope?` | — | FEAT-26 |
| `/api/review/propose` | propose → `propose_flow` | `client_id, scenario, title, option` | — | FEAT-27 |
| `/api/review/decide` | decide → `review_flow` | `item_id, decision (approved\|rejected), note?, by` | RM | FEAT-27 |
| `/api/news/ingest` | news_fetch → `ingest_flow` | `{}` | CIO (the person signed in) | FEAT-01 |
| `/api/news/dismiss` | news_dismiss → `dismiss_flow` | `ids, by?, note?` | CIO | FEAT-02 |
| `/api/news/release` | news_release → `release_flow` | `item_id, by, note` | Compliance | FEAT-02 |
| `/api/events` | event → `event_flow` | `news_ids, title?, by` | CIO | FEAT-02 |
| `/api/events/run-agent` | cio_agent → `agent_queue_flow` (a job; the `agent_worker` job runs `cio_agent_flow`) | `event_id, by, mode? (live\|mock)` → `{job}` | CIO; 409 in inbox mode or on a held event | FEAT-04, 05 |
| `/api/views/decide` | view_decide → `decide_flow` | `view_id, action, by, reason, idem_key?, edits?, responses?` | CIO | FEAT-06 |
| `/api/runs/recompute` | run_recompute → `recompute_flow` | `run, by, idem_key?` | CIO | FEAT-08 |
| `/api/runs/decide` | run_decide → `run_decide_flow` | `run, action (make_effective\|withdraw), by, reason` | CIO | FEAT-08 |
| `/api/research` | research_upload → `research_upload_flow` | `item {kind, report_no, title, summary, release_at, conflict? {related, parties, statement}, regulation?}, by` (naming a related party needs `conflict`) | CIO | FEAT-03 |
| `/api/research/release` | research_release → `research_release_flow` | `item_id, decision (release\|reject), by, note` | Compliance, ≠ uploader | FEAT-03 |
| `/api/newsletters` | newsletter_draft → `newsletter_draft_flow` | `view_ids (1–6 approved), by, title?, mode (template\|agent)?, distribution? {send_at, private_early_hours, early_reason}, conflict?` | CIO | FEAT-17 |
| `/api/policy` | policy_add → `policy_add_flow` | `item {gazette_url} \| {source_url (official), title, number?, issuer?, issued?, text?, status, note?}, by` | Compliance | FEAT-16 |
| `/api/policy/verify` | policy_verify → `policy_verify_flow` | `document_id, by, note (≥ 20)` | Compliance, ≠ the one who added it | FEAT-16 |
| `/api/policy/status` | policy_status → `policy_status_flow` | `document_id, status (draft\|consultation\|issued\|effective\|dropped), by, note (≥ 10), date?` | Compliance | FEAT-16 |
| `/api/policy/summarise` | policy_summarise → `policy_summarise_flow` | `document_id, by, mode?` (verified documents only; 409 with why otherwise) | Compliance | FEAT-16 |
| `/api/newsletters/act` | newsletter_act → `newsletter_act_flow` | `newsletter_id, action (edit\|submit\|withdraw: CIO; approve\|return: Compliance, ≠ author), by, note?, changes? {title, intro, headings, distribution, conflict}` | CIO, Compliance | FEAT-17 |
| `/api/goals/outflow` | goal_outflow → `goal_outflow_flow` | `family_id, goal_id, purpose, country?, by` | RM | FEAT-10 |
| `/api/system/alerts/ack` | alert_ack → `alert_ack_flow` | `alert_id, by, note?` | a role the alert's kind is for (CIO, Compliance, Admin); 409 if not open | FEAT-36 |
| `/api/market/load` | market_load_ask → `market_load_ask_flow` | `by, since? (YYYY-MM-DD, from 2015-01-01; default 2020-01-01)` | Admin | FEAT-12 (SCR-ADM-01) |
| `/api/reset` | web (`reset`) | — | — | demo reset |

## The AI zone's doors (FEAT-19, [ADR-0022](../decisions/ADR-0022-the-ai-zone-is-a-second-process.md))

| Path | Process | Body | Answers |
|---|---|---|---|
| `POST /api/inbox` | the bank (`app/web.py`), open without a session: the signature is the check | a package (FEAT-19), header `x-mf-signature: sha256=<hex>` (`MF_INBOX_KEY`) | `202 {"id"}` only; 409 outside inbox mode, 413 over 512 KB, 429 with 200 waiting |
| `POST /api/zone/sync` | the AI zone (`src/zone/web.py`) | the bank's bundle `{version, catalogues, not_set, research}`, signed `MF_ZONE_KEY` | `{applied, research_added}`; 401 unsigned, 400 a catalogue that may not go or fails its check |
| `GET /api/zone/status` | the AI zone | — | its news count, last ingest, catalogues in force (and from which bank version), today's events and cap, the outbox |

## Sign-in (`app/web.py`, FEAT-12)

Every `/api/*` path but these needs a session (401 without one). Each read is open to the roles `ROUTE_ROLES` in
`app/web.py` names for its path (403 otherwise; the matrix is in `tests/test_access.py`), and a family's data only to
whoever may see it ([ADR-0020](../decisions/ADR-0020-sign-in-with-own-accounts.md)). A served action that refuses
answers 403 with the reason, not signed in 401, a bad value 400 (operonx 1.27 `http_status`).

| Path | Body / query | Returns |
|---|---|---|
| `GET /api/auth/me` | — | `user` (id, name, role, title, `family` for a customer, `families` for an RM) or null; `auth` (sign-in on); `demo_accounts` |
| `POST /api/auth/login` | `login` (e-mail or id), `password` | `user`, and the session cookie; 401 with one answer for any failure |
| `POST /api/auth/demo` | `id` | as login, for a listed demo account; 403 unless `MF_DEMO_ACCOUNTS=on` |
| `POST /api/auth/logout` | — | clears the cookie |
| `GET /api/auth/accounts` | — | the demo accounts (id, name, role, title, login), empty unless `MF_DEMO_ACCOUNTS=on` |

## Reads (GET, `app/web.py`)

| Path | Query | Returns | Feature |
|---|---|---|---|
| `/healthz` | — | liveness, and each protection on or off (`protections`, `off`) | FEAT-11, 12 |
| `/api/clients` | — | the families the person signed in may see | FEAT-20, 12 |
| `/api/agents/catalogue` | `days (1–365, default 7)` | FR-703 catalogue, open-source references, RULE-MEAS-04 quality | FEAT-15 |
| `/api/config`, `/api/config/{id}` | — | every kind with its version in force, pending proposal and history; one version | FEAT-14 |
| `/api/scenarios` | — | the scenario catalogue (id, kind, title, question, personas) | FEAT-26 |
| `/api/review` | `client_id?, status?` | the RM queue, of the families the person may see | FEAT-27 |
| `/api/advisory` | `client_id` | a client's specialist team and record (mock) | FEAT-28 |
| `/api/advisory/all` | — | the record over the person's clients (an RM: theirs; mock) | FEAT-28 |
| `/api/views` | — | house views (mock) | FEAT-25 |
| `/api/news/inbox` | `source, kind, status (default new), relevance, since, q, held, limit (≤ 1000)` | inbox items and feed health | FEAT-01, 02 |
| `/api/news/config` | — | white list and restricted list | FEAT-02 |
| `/api/model` | — | the factor model (factors, sizes, realisation, vols, stress repair) | FEAT-07 |
| `/api/events`, `/api/events/{id}` | — | events with their views | FEAT-02, 04 |
| `/api/views/{id}` | — | a view with findings, decisions, agent runs, checks, preview | FEAT-04…06 |
| `/api/agents` | — | mode, models, prompt version, demo users | FEAT-15, 12 |
| `/api/runs` | `role? (rm), view_id?` | runs, newest first | FEAT-08 |
| `/api/runs/{id}`, `/api/runs/{id}/verify` | — | a run; its recomputation compared to the dong | FEAT-08 |
| `/api/families/{id}/impact` | `role (default client)` | the family's impact as that role may see it (403 for an unknown role); each item has a `timeline` of its steps with their stored times | FEAT-13, FEAT-30 |
| `/api/families/{id}/graph` | `role (default client)`, `run_id?` | news → … → goal nodes and edges with their stored sources (403 for an unknown role); an event node names its `run`, an asset → family edge its `by_run` shares | FEAT-30 |
| `/api/runs/{id}/graph` | — | the whole run: news → event → scenario → factor → asset class → every family (404 for an unknown run) | FEAT-30 (R4) |
| `/api/trace/{run_id}/{family_id}` | `key?, horizon? (3m)` | the trace (404 if unknown) | FEAT-09 |
| `/api/families/{id}/how` | `run` | the client's “Cách tính” for one effective run: number and band, formula, scenarios with factor moves, asset classes, event type, outlets; no holding or headline (404 if the run is not effective or has no such family) | FEAT-09, FEAT-13 |
| `/api/rm/today` | — | flagged cases and goal tasks | FEAT-13, 10 |
| `/api/audit`, `/api/audit/verify` | `limit (≤ 1000)` | log rows; chain check | FEAT-11 |
| `/api/audit/export` | `format=json\|csv` | the whole chain as a download (JSON includes the check) | FEAT-11 |
| `/api/market` | — | staff: the market jobs (cadence, last run, last success, last error), each series' coverage, last value, source and 120-day tail, each factor's provenance | FEAT-35 |
| `/api/market/series` | `id, from?` | staff: one stored or computed (DXY, SJC_GAP) series' points | FEAT-35 |
| `/api/system/alerts` | `role?` (sign-in off) | CIO, Compliance, Admin: the open and acknowledged alerts of the kinds the role looks after (the bell) | FEAT-36 |
| `/api/system` | — | Admin: jobs and how each last went, news feeds, agent runs (7 days) and runs queued, audit chain check, history loads, the inbox's packages and the last zone syncs, the last 30 alerts and the central log's last 30 warnings and errors, configuration waiting, staff accounts with an RM's families | FEAT-12 (SCR-ADM-01) |
| `/api/accuracy` | — | staff: the model walked forward over history (per horizon and factor: observations, share inside P10–P90, verdict, direction hit rate; KPI-03), the approved views' forecasts summarised and listed with their scores | FEAT-18 |
| `/api/measure` | — | staff: the monthly reports — misses with causes, approvals (minutes, without edits, under 2 min), news to RM hours, inbox and CIO agent minutes | FEAT-18 |
| `/api/research` | `status?` | research items and kinds | FEAT-03 |
| `/api/newsletters` | — | CIO, Compliance: the letters (without their sections) and the approved views to draft from | FEAT-17 |
| `/api/policy` | `since?` | CIO, Compliance: the radar — documents by last change (no text), new / changed since `since`, counts by status | FEAT-16 |
| `/api/policy/{id}` | — | CIO, Compliance: one document with its text, articles, history, verification and the agent's summary | FEAT-16 |
| `/api/newsletters/{id}` | — | CIO, Compliance: one letter — sections, labels, the guard's result, distribution, history | FEAT-17 |
| `/api/goals/regulation` | `family_id?, role?` | regulation matches, purposes, a family's goals (staff) | FEAT-10 |

## Differences from the BRD's endpoint list (§12.3)

The BRD lists its author's endpoints (e.g. `POST /api/events/from-news`, `PUT /api/views/:id/scenarios`,
`POST /api/views/:id/decision`, `GET /api/families/:id/impacts`, `GET /api/config`, `POST /api/external/import`).
Here the same operations are named differently (one decision endpoint with `action`, edits through it) and these
have no equivalent: `/cashflow` and `/pnl` per family as separate reads (they are part of `/api/dashboard`),
`GET/POST /api/config` (FEAT-14), `POST /api/external/import` and `/api/external/submit` (FEAT-19: here the
zone's `POST /api/inbox` and the `inbox_import` job),
`GET /api/procedural` (here `/api/goals/regulation`).

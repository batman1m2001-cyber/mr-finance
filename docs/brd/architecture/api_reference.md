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
| `/api/feed` | feed → `feed_flow` | `client_id, scope?, role? (client\|rm)` | — | FEAT-31 |
| `/api/copilot` | copilot → `copilot_flow` | `question, role, client_id?, scope?, route?, confirm?` | per tool (and the wrapped graph's own check) | FEAT-32 |
| `/api/statement` | statement → `statement_flow` | `client_id, filename, content` (base64) | — | FEAT-22 |
| `/api/declare` | declare → `declare_flow` | `client_id, message, session_id` | — | FEAT-23 |
| `/api/risk` | risk → `risk_flow` | `client_id, answers` | — | FEAT-24 |
| `/api/alerts` | alerts → `alerts_flow` | `client_id, scope?` | — | FEAT-25 |
| `/api/scenario` | scenario → `scenario_flow` | `client_id, scenario, params?, scope?` | — | FEAT-26 |
| `/api/goals` | goals → `goals_flow` | `client_id, scope?` | — | FEAT-26 |
| `/api/review/propose` | propose → `propose_flow` | `client_id, scenario, title, option` | — | FEAT-27 |
| `/api/review/decide` | decide → `review_flow` | `item_id, decision (approved\|rejected), note?, by` | RM | FEAT-27 |
| `/api/news/ingest` | news_fetch → `ingest_flow` | `{}` | — | FEAT-01 |
| `/api/news/dismiss` | news_dismiss → `dismiss_flow` | `ids, by?, note?` | CIO | FEAT-02 |
| `/api/news/release` | news_release → `release_flow` | `item_id, by, note` | Compliance | FEAT-02 |
| `/api/events` | event → `event_flow` | `news_ids, title?, by` | CIO | FEAT-02 |
| `/api/events/run-agent` | cio_agent → `cio_agent_flow` | `event_id, by, mode? (live\|mock)` | CIO | FEAT-04, 05 |
| `/api/views/decide` | view_decide → `decide_flow` | `view_id, action, by, reason, idem_key?, edits?, responses?` | CIO | FEAT-06 |
| `/api/runs/recompute` | run_recompute → `recompute_flow` | `run_id, by, idem_key?` | CIO | FEAT-08 |
| `/api/runs/decide` | run_decide → `run_decide_flow` | `run_id, action (make_effective\|withdraw), by, reason` | CIO | FEAT-08 |
| `/api/research` | research_upload → `research_upload_flow` | `item {kind, report_no, title, summary, release_at, conflicts?, regulation?}, by` | CIO | FEAT-03 |
| `/api/research/release` | research_release → `research_release_flow` | `item_id, decision (release\|reject), by, note` | Compliance, ≠ uploader | FEAT-03 |
| `/api/goals/outflow` | goal_outflow → `goal_outflow_flow` | `family_id, goal_id, purpose, country?, by` | RM | FEAT-10 |
| `/api/reset` | web (`reset`) | — | — | demo reset |

## Reads (GET, `app/web.py`)

| Path | Query | Returns | Feature |
|---|---|---|---|
| `/healthz` | — | liveness, and each protection on or off (`protections`, `off`) | FEAT-11, 12 |
| `/api/clients` | — | the sample clients | FEAT-20 |
| `/api/scenarios` | — | the scenario catalogue (id, kind, title, question, personas) | FEAT-26 |
| `/api/review` | `client_id?, status?` | the RM queue | FEAT-27 |
| `/api/advisory` | `client_id` | a client's specialist team and record (mock) | FEAT-28 |
| `/api/advisory/all` | — | the record over all clients (mock) | FEAT-28 |
| `/api/views` | — | house views (mock) | FEAT-25 |
| `/api/news/inbox` | `source, kind, status (default new), relevance, since, q, held, limit (≤ 1000)` | inbox items and feed health | FEAT-01, 02 |
| `/api/news/config` | — | white list and restricted list | FEAT-02 |
| `/api/model` | — | the factor model (factors, sizes, realisation, vols, stress repair) | FEAT-07 |
| `/api/events`, `/api/events/{id}` | — | events with their views | FEAT-02, 04 |
| `/api/views/{id}` | — | a view with findings, decisions, agent runs, checks, preview | FEAT-04…06 |
| `/api/agents` | — | mode, models, prompt version, demo users | FEAT-15, 12 |
| `/api/runs` | `role? (rm), view_id?` | runs, newest first | FEAT-08 |
| `/api/runs/{id}`, `/api/runs/{id}/verify` | — | a run; its recomputation compared to the dong | FEAT-08 |
| `/api/families/{id}/impact` | `role (default client)` | the family's impact as that role may see it (403 for an unknown role) | FEAT-13 |
| `/api/families/{id}/graph` | `role (default client)`, `run_id?` | news → … → goal nodes and edges with their stored sources (403 for an unknown role) | FEAT-30 |
| `/api/trace/{run_id}/{family_id}` | `key?, horizon? (3m)` | the trace (404 if unknown) | FEAT-09 |
| `/api/rm/today` | — | flagged cases and goal tasks | FEAT-13, 10 |
| `/api/audit`, `/api/audit/verify` | `limit (≤ 1000)` | log rows; chain check | FEAT-11 |
| `/api/audit/export` | `format=json\|csv` | the whole chain as a download (JSON includes the check) | FEAT-11 |
| `/api/research` | `status?` | research items and kinds | FEAT-03 |
| `/api/goals/regulation` | `family_id?, role?` | regulation matches, purposes, a family's goals (staff) | FEAT-10 |

## Differences from the BRD's endpoint list (§12.3)

The BRD lists its author's endpoints (e.g. `POST /api/events/from-news`, `PUT /api/views/:id/scenarios`,
`POST /api/views/:id/decision`, `GET /api/families/:id/impacts`, `GET /api/config`, `POST /api/external/import`).
Here the same operations are named differently (one decision endpoint with `action`, edits through it) and these
have no equivalent: `/cashflow` and `/pnl` per family as separate reads (they are part of `/api/dashboard`),
`GET/POST /api/config` (FEAT-14), `POST /api/external/import` and `/api/external/submit` (FEAT-19),
`GET /api/procedural` (here `/api/goals/regulation`).

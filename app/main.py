"""Mr. Finance: the whole picture of a client's wealth, and what is moving it.

POST /api/dashboard {client_id, scope?, months?} ──► pages_flow ──► the dashboard
POST /api/flows     {client_id, scope?, month?} ──► flows_flow ──► a month's money in → out, with the rows
POST /api/timeline  {client_id, scope?, node, unit?} ──► timeline_flow ──► a graph node's money by day, month, year
POST /api/feed      {client_id, scope?, role?} ──► feed_flow ──► what matters now, why, and its evidence
POST /api/feed/open {client_id, key} ──► feed_open_flow ──► the client opened a high-level item (KPI-07)
POST /api/rm/contacts {family_id, channel, signal?, note?, by} ──► contact_flow ──► an RM's contact (KPI-06)
POST /api/copilot   {question, role, client_id?, scope?, route?, confirm?} ──► assistant_flow (copilot) ──► a templated answer
POST /api/assistant {message | turn_id + approvals, role, client_id?, scope?, route?, conversation_id?} ──►
                    assistant_flow ──► an answer from the role's tools in several steps; writes wait for the person
                    (A2); kept in its conversation (A3) · POST /api/assistant/conversations ──► list, open, delete
                    · POST /api/assistant/memory ──► the Bộ nhớ page (A4) · 02:30 daily ──► assistant_retention
                    · POST /api/assistant/attach ──► a file or image, read once (OCR_PLAN)
                    · every 5 min ──► assistant_consolidate (A6) · market and news jobs ──► follow-ups (A6)
WS   /api/assistant/voice?rate= ──► assistant_voice_flow ──► the assistant by voice: microphone PCM in, captions,
                    the question and the answer read sentence by sentence out (docs/VOICE_PLAN.md)
POST /api/config/propose, /api/config/decide ──► versioned configuration, propose then approve (FR-701)
POST /api/statement {client_id, filename, content} ──► intake_flow (action statement) ──► holdings read (AI or rules)
POST /api/declare   {client_id, message, session_id} ──► intake_flow (action declare) ──► the chat's reply, what it recorded
POST /api/declare/stream (same body, text/event-stream) ──► declare_stream_flow ──► the same turn as it happens
POST /api/risk      {client_id, answers} ──► risk_flow ──► the next question, or the profile
POST /api/alerts    {client_id, scope?} ──► news_flow (alerts) ──► policies, macro, infrastructure, in VND
POST /api/scenario  {client_id, scenario, params?} ──► scenarios_flow (action scenario) ──► numbers, a light and a heavy option
POST /api/goals     {client_id, scope?} ──► scenarios_flow (action goals) ──► every life goal: need, have, gap, status, actions
POST /api/allocation {client_id, scope?, method?, assumptions?, role?, whatif?} ──► allocation_flow ──► Liquidity, Legacy,
                    Growth: targets, gaps, the actions, checked (ASSET_ALLOCATION_BRD) · /api/allocation/example ──►
                    the worked example K-7F3A · /api/allocation/tilt ──► a CIO tilts the model from an approved view ·
                    /api/allocation/send ──► an RM sends the actions to the review queue ·
                    /api/allocation/review ──► the CIO decides each action (Q-29), /api/allocation/queue lists them ·
                    /api/allocation/override ──► an RM moves an asset to another bucket, with a reason ·
                    /api/allocation/method ──► the CIO picks ±2-point tilts or Black–Litterman
POST /api/evidence {factor?, role?} ──► evidence_flow (one flow, an action per route) ──► each item's evidence: statistics or the qualitative frame
                    (NEWS_EVIDENCE_BRD) · /api/evidence/decide ──► the CIO approves, returns or rejects a frame
                    · /api/evidence/draft ──► the agent drafts a news item's frame · /draft/decide ──► the CIO reviews it
                    · /api/evidence/type ──► the CIO adds an event type or precedent dates (P2)
POST /api/scenario/combine {client_id, scenarios, params?} ──► scenarios_flow (action combine) ──► stress tests together
POST /api/review/propose (the RM queue), /decide, /recommend (the RM's own recommendation) ──► review_flow
07:00 daily, and `operonx run policy_sweep` ──► the policy_sweep job: news_flow (alerts) for every client
every 10 min, POST /api/news/ingest, `operonx run news_ingest` ──► news_flow (ingest): the feeds into the inbox
every 2 h ──► news_reference: the independent reference's stories, judged collected a day later (KPI-02)
15:45/16:00/17:30 daily and hourly, `operonx run market_<kind>` ──► the market jobs: public sources into SQLite
     (market_backfill on demand) · GET /api/market[/series] ──► app/web.py (the source registry, the series)
POST /api/news/dismiss, /api/news/release ──► news_flow (a CIO)
GET  /api/news/inbox ──► app/web.py (the inbox and the feed-health strip)
POST /api/events, /api/events/urgent ──► news_flow (KPI-01) · POST /api/events/run-agent
     ──► news_flow (queue), then the agent_worker job ──► cio_agent_flow (agent + challenger)
POST /api/newsletters, /api/newsletters/act ──► research_flow, a task each (FR-801: the CIO drafts from
     approved views, another CIO approves, a preview, never sent) · GET /api/newsletters[/{id}] ──► app/web.py
POST /api/policy[/verify|/status|/summarise] ──► policy_flow, an action each (FR-306: a CIO adds a document from the Official
     Gazette, a second CIO verifies it, the policy agent quotes it) · GET /api/policy[/{id}] (radar) ──► app/web.py
Every 20 s ──► heartbeat: the minute recorded, availability in business hours (NFR-03)
Hourly ──► audit_check: the audit chain walked, new rows to write-once segments · POST /api/system/alerts/ack ──►
     admin_flow (task alert_ack); GET /api/system/alerts (the bell) — alerts on failing feeds, series, agents, the chain, the
     inbox, availability (NFR-12)
POST /api/inbox ◄── the AI zone (app/zone.py, its own process and database) ──► the inbox_import job every 10 min;
     the zone_sync job sends the zone the approved catalogues and released research (inbox mode, F-D7)
POST /api/views/decide ──► review_flow · GET /api/events[/{id}], /api/views/{id}, /api/agents ──► app/web.py
approve ──► an application run for every family · POST /api/runs/recompute, /api/runs/decide ──► review_flow ·
     GET /api/runs[/{id}[/verify]], /api/families/{id}/impact?role=, /api/trace/{run}/{family},
     /api/rm/today, /api/audit[/verify] ──► app/web.py
POST /api/research, /api/research/release, /api/goals/outflow, /api/goals/suggest ──► research_flow, a task each ·
     GET /api/research, /api/goals/regulation ──► app/web.py
GET  /api/clients, /api/advisory[/all], /api/views, POST /api/reset, GET / ──► app/web.py (the sample
     clients, the RM team, the advisory track record, the house views, the UI)

Each service runs its graph as is: the JSON body fills the graph's parameters, and the reply is
its outputs (`{"dashboard": ...}`, `{"read": ...}`, ...). Each feature declares its services, jobs and
request contracts in app/<feature>.py (src/ computes, app/ exposes); this module collects them into `APP`,
with what belongs to the whole app: the middleware, the web mount, the client-data barrier.
operonx.toml only points at `APP`.
"""

from operonx.app import Application, Service, asgi

from app import (
    allocation,
    assistant,
    control,
    evidence,
    market,
    news,
    pages,
    policy,
    research,
    review,
    scenarios,
    statements,
    web,
)
from app.http import SecurityHeaders
from app.serve import PORT
from control import barrier
from control import jobs as control_jobs

barrier.install()  # every llm: call of this process passes the client-data barrier (BRD-NFR-08)

APP = Application(
    "mr-finance",
    description="Consolidate every asset a client holds, anywhere, into one picture — and say what is moving it.",
    middleware=[SecurityHeaders],  # every response: security headers, no cross-site writes (BRD-NFR-07)
    services=[
        *pages.SERVICES,
        *control.SERVICES,
        *assistant.SERVICES,
        *statements.SERVICES,
        *news.SERVICES,
        *scenarios.SERVICES,
        *allocation.SERVICES,
        *evidence.SERVICES,
        *review.SERVICES,
        *research.SERVICES,
        *policy.SERVICES,
        # last: it is mounted at "/", and would answer every path the services above own
        Service("web", asgi("/", port=PORT), app=web.app, description="The UI and the sample clients."),
    ],
    jobs=[*news.JOBS, *assistant.JOBS, *market.JOBS, *control.JOBS, *statements.JOBS],
)

# Hệ thống lists the jobs as declared here (app/web.py cannot import this module); Việc nền runs them (control/jobs.py)
control_jobs.register(APP.jobs)
web.JOBS[:] = [
    {"id": j.name, "description": j.description, "when": (j.schedule.options if j.schedule else {})} for j in APP.jobs
]

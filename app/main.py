"""Mr. Finance: the whole picture of a client's wealth, and what is moving it.

POST /api/dashboard {client_id, scope?, months?} ──► dashboard_flow ──► the dashboard
POST /api/flows     {client_id, scope?, month?} ──► flows_flow ──► a month's money in → out, with the rows
POST /api/timeline  {client_id, scope?, node, unit?} ──► timeline_flow ──► a graph node's money by day, month, year
POST /api/feed      {client_id, scope?, role?} ──► feed_flow ──► what matters now, why, and its evidence
POST /api/feed/open {client_id, key} ──► feed_open_flow ──► the client opened a high-level item (KPI-07)
POST /api/rm/contacts {family_id, channel, signal?, note?, by} ──► contact_flow ──► an RM's contact (KPI-06)
POST /api/copilot   {question, role, client_id?, scope?, route?, confirm?} ──► copilot_flow ──► a templated answer
POST /api/assistant {message | turn_id + approvals, role, client_id?, scope?, route?, conversation_id?} ──►
                    assistant_flow ──► an answer from the role's tools in several steps; writes wait for the person
                    (A2); kept in its conversation (A3) · POST /api/assistant/conversations ──► list, open, delete
                    · POST /api/assistant/memory ──► the Bộ nhớ page (A4) · 02:30 daily ──► assistant_retention
                    · POST /api/assistant/attach ──► a file or image, read once (OCR_PLAN)
                    · every 5 min ──► assistant_consolidate (A6) · market and news jobs ──► follow-ups (A6)
POST /api/config/propose, /api/config/decide ──► versioned configuration, propose then approve (FR-701)
POST /api/statement {client_id, filename, content} ──► statement_flow ──► holdings read (AI or rules)
POST /api/declare   {client_id, message, session_id} ──► declare_flow ──► the chat's reply, what it recorded
POST /api/declare/stream (same body, text/event-stream) ──► declare_stream_flow ──► the same turn as it happens
POST /api/risk      {client_id, answers} ──► risk_flow ──► the next question, or the profile
POST /api/alerts    {client_id, scope?} ──► alerts_flow ──► policies, macro, infrastructure, in VND
POST /api/scenario  {client_id, scenario, params?} ──► scenario_flow ──► numbers, a light and a heavy option
POST /api/goals     {client_id, scope?} ──► goals_flow ──► every life goal: need, have, gap, status, actions
POST /api/scenario/combine {client_id, scenarios, params?} ──► combine_flow ──► stress tests together
POST /api/review/propose ──► propose_flow (the RM queue) · POST /api/review/decide ──► review_flow
POST /api/review/recommend ──► recommend_flow (the RM's own recommendation)
07:00 daily, and `operonx run policy_sweep` ──► the policy_sweep job: alerts_flow for every client
every 10 min, POST /api/news/ingest, `operonx run news_ingest` ──► ingest_flow: the feeds into the inbox
every 2 h ──► news_reference: the independent reference's stories, judged collected a day later (KPI-02)
15:45/16:00/17:30 daily and hourly, `operonx run market_<kind>` ──► the market jobs: public sources into SQLite
     (market_backfill on demand) · GET /api/market[/series] ──► app/web.py (the source registry, the series)
POST /api/news/dismiss ──► dismiss_flow · POST /api/news/release ──► release_flow (a CIO)
GET  /api/news/inbox ──► app/web.py (the inbox and the feed-health strip)
POST /api/events ──► event_flow · POST /api/events/urgent ──► event_urgent_flow (KPI-01) · POST /api/events/run-agent
     ──► agent_queue_flow, then the agent_worker job ──► cio_agent_flow (agent + challenger)
POST /api/newsletters, /api/newsletters/act ──► newsletter_draft_flow, newsletter_act_flow (FR-801: the CIO drafts from
     approved views, another CIO approves, a preview, never sent) · GET /api/newsletters[/{id}] ──► app/web.py
POST /api/policy[/verify|/status|/summarise] ──► policy_*_flow (FR-306: a CIO adds a document from the Official
     Gazette, a second CIO verifies it, the policy agent quotes it) · GET /api/policy[/{id}] (radar) ──► app/web.py
Every 20 s ──► heartbeat: the minute recorded, availability in business hours (NFR-03)
Hourly ──► audit_check: the audit chain walked, new rows to write-once segments · POST /api/system/alerts/ack ──►
     alert_ack_flow; GET /api/system/alerts (the bell) — alerts on failing feeds, series, agents, the chain, the
     inbox, availability (NFR-12)
POST /api/inbox ◄── the AI zone (app/zone.py, its own process and database) ──► the inbox_import job every 10 min;
     the zone_sync job sends the zone the approved catalogues and released research (inbox mode, F-D7)
POST /api/views/decide ──► decide_flow · GET /api/events[/{id}], /api/views/{id}, /api/agents ──► app/web.py
approve ──► an application run for every family · POST /api/runs/recompute, /api/runs/decide ──► recompute_flow,
     run_decide_flow · GET /api/runs[/{id}[/verify]], /api/families/{id}/impact?role=, /api/trace/{run}/{family},
     /api/rm/today, /api/audit[/verify] ──► app/web.py
POST /api/research, /api/research/release, /api/goals/outflow ──► the research and goal-branch flows ·
     GET /api/research, /api/goals/regulation ──► app/web.py
GET  /api/clients, /api/advisory[/all], /api/views, POST /api/reset, GET / ──► app/web.py (the sample
     clients, the RM team, the advisory track record, the house views, the UI)

Each service runs its graph as is: the JSON body fills the graph's parameters, and the reply is
its outputs (`{"dashboard": ...}`, `{"read": ...}`, ...). Every service and job of the product is
declared here; operonx.toml only points at `APP`.
"""

import os

from operonx.app import Application, Eval, Service, asgi, env, http
from operonx.app import schedule as _schedule
from operonx.app.evals import Gate
from operonx.app.jobs import Job

from app import web
from app.http import SecurityHeaders
from apply.graph import recompute_flow, run_decide_flow
from assistant.graph import (
    assistant_consolidate_flow,
    assistant_conversations_flow,
    assistant_flow,
    assistant_attach_flow,
    assistant_memory_flow,
    assistant_retention_flow,
    assistant_stream_flow,
)
from contacts.graph import contact_flow
from control import barrier
from control import jobs as control_jobs
from control.graph import (
    alert_ack_flow,
    audit_check_flow,
    config_decide_flow,
    config_propose_flow,
    heartbeat_flow,
    job_run_flow,
)
from copilot.graph import copilot_flow
from dashboard.graph import dashboard_flow
from declare.graph import declare_flow, declare_stream_flow
from events.graph import event_flow, event_urgent_flow
from feed.graph import feed_flow, feed_open_flow
from flows.graph import flows_flow
from impact.graph import alerts_flow
from impact.ops import every_client
from inbox.graph import inbox_import_flow
from market.graph import (
    market_backfill_flow,
    market_crypto_flow,
    market_equity_flow,
    market_flows_flow,
    market_fx_flow,
    market_gold_flow,
    market_load_ask_flow,
    market_load_flow,
    market_world_flow,
    market_yields_flow,
    model_estimate_flow,
)
from measure.graph import accuracy_flow
from news.graph import dismiss_flow, ingest_flow, reference_flow, release_flow
from newsletter.graph import newsletter_act_flow, newsletter_draft_flow
from overview.graph import overview_flow
from people.graph import account_decide_flow, account_request_flow
from policy.graph import policy_add_flow, policy_status_flow, policy_summarise_flow, policy_verify_flow
from research.graph import goal_outflow_flow, research_release_flow, research_upload_flow
from review.graph import propose_flow, recommend_flow, review_flow
from risk.graph import risk_flow
from scenarios.graph import combine_flow, goals_flow, scenario_flow
from search.graph import search_flow
from statements.checks import items_match
from statements.graph import sample_flow, statement_flow
from timeline.graph import timeline_flow
from trial.graph import trial_daily_flow, trial_score_flow
from views.graph import agent_eval_flow, agent_queue_flow, agent_worker_flow, decide_flow
from zone.graph import zone_sync_flow

barrier.install()  # every llm: call of this process passes the client-data barrier (BRD-NFR-08)

PORT = env("PORT", 8030)


def schedule(**kw):
    """A job's clock — none with MF_JOBS=off (a second copy of the app, e.g. an experiment, runs no job on its
    own: no fetch and no model call twice; each still runs with `operonx run <job>`)."""
    return None if os.environ.get("MF_JOBS", "").lower() == "off" else _schedule(**kw)


APP = Application(
    "mr-finance",
    description="Consolidate every asset a client holds, anywhere, into one picture — and say what is moving it.",
    middleware=[SecurityHeaders],  # every response: security headers, no cross-site writes (BRD-NFR-07)
    services=[
        Service(
            "dashboard",
            http("POST", "/api/dashboard", port=PORT),
            graph=dashboard_flow,
            description="POST {client_id, scope: personal|family, months}: the dashboard.",
        ),
        Service(
            "overview",
            http("POST", "/api/overview", port=PORT),
            graph=overview_flow,
            description="POST {client_id, scope, role: client|rm, goals}: the overview graph around one client.",
        ),
        Service(
            "timeline",
            http("POST", "/api/timeline", port=PORT),
            graph=timeline_flow,
            description="POST {client_id, scope, node, unit: day|month|year}: a node's money over time (simulated).",
        ),
        Service(
            "flows",
            http("POST", "/api/flows", port=PORT),
            graph=flows_flow,
            description="POST {client_id, scope: personal|family, month: YYYY-MM}: Money Flow from the transactions.",
        ),
        Service(
            "feed",
            http("POST", "/api/feed", port=PORT),
            graph=feed_flow,
            description="POST {client_id, scope, role: client|rm}: the Intelligence Feed, with why and evidence.",
        ),
        Service(
            "feed_open",
            http("POST", "/api/feed/open", port=PORT),
            graph=feed_open_flow,
            description="POST {client_id, key}: the client opened a high-level item (KPI-07).",
        ),
        Service(
            "rm_contact",
            http("POST", "/api/rm/contacts", port=PORT),
            graph=contact_flow,
            description="POST {family_id, channel, signal?, note?, by}: an RM records a contact, from a Hôm nay "
            "signal or not (KPI-06).",
        ),
        Service(
            "config_propose",
            http("POST", "/api/config/propose", port=PORT),
            graph=config_propose_flow,
            description="POST {kind, data, by, note}: propose a configuration version (FR-701).",
        ),
        Service(
            "config_decide",
            http("POST", "/api/config/decide", port=PORT),
            graph=config_decide_flow,
            description="POST {version_id, action: approve|reject, by, note}: decide a proposed version.",
        ),
        Service(
            "search",
            http("POST", "/api/search", port=PORT),
            graph=search_flow,
            description="POST {q, role, client_id?, scope?}: the header search over what the role may open.",
        ),
        Service(
            "copilot",
            http("POST", "/api/copilot", port=PORT),
            graph=copilot_flow,
            description="POST {question, role, client_id, scope, route, confirm}: the Copilot (routes, never reads).",
        ),
        Service(
            "assistant",
            http("POST", "/api/assistant", port=PORT),
            graph=assistant_flow,
            description="POST {message | turn_id + approvals, role, client_id, scope, route, goals, conversation_id}: "
            "the assistant (A2) — the role's tools in several steps, writes confirmed and verified, kept in a "
            "conversation (A3); the Copilot's path when no model answers.",
        ),
        Service(
            "assistant_stream",
            http("POST", "/api/assistant/stream", port=PORT),
            graph=assistant_stream_flow,
            description="POST the same body as /api/assistant, Accept: text/event-stream: the turn as it happens — "
            "step (a tool starting and ending, with the graph nodes it reads), text, wait, then the answer (FEAT-40).",
        ),
        Service(
            "assistant_conversations",
            http("POST", "/api/assistant/conversations", port=PORT),
            graph=assistant_conversations_flow,
            description="POST {action: list | open | delete, conversation_id, role, client_id}: the person's "
            "conversations with the assistant (A3).",
        ),
        Service(
            "assistant_memory",
            http("POST", "/api/assistant/memory", port=PORT),
            graph=assistant_memory_flow,
            description="POST {action: list | search | update | delete | clear, item_id, text, kind, query, role, "
            "client_id}: the Bộ nhớ page (A4).",
        ),
        Service(
            "assistant_attach",
            http("POST", "/api/assistant/attach", port=PORT),
            graph=assistant_attach_flow,
            description="POST {file_name, data: base64, role, client_id}: a file or image for the assistant, read "
            "once and kept 24 hours (docs/OCR_PLAN.md).",
        ),
        Service(
            "statement",
            http("POST", "/api/statement", port=PORT),
            graph=statement_flow,
            description="POST {client_id, filename, content: base64}: a statement, read and kept.",
        ),
        Service(
            "declare",
            http("POST", "/api/declare", port=PORT),
            graph=declare_flow,
            description="POST {client_id, message, session_id}: one chat turn of declarations.",
        ),
        Service(
            "declare_stream",
            http("POST", "/api/declare/stream", port=PORT),
            graph=declare_stream_flow,
            description="POST the same body as /api/declare, Accept: text/event-stream: the turn as it happens — "
            "step, text, form (what the agent asks back), then the answer.",
        ),
        Service(
            "risk",
            http("POST", "/api/risk", port=PORT),
            graph=risk_flow,
            description="POST {client_id, answers}: the next question of the risk test, or its result.",
        ),
        Service(
            "alerts",
            http("POST", "/api/alerts", port=PORT),
            graph=alerts_flow,
            description="POST {client_id, scope?}: what is moving the client's wealth, in VND, with sources.",
        ),
        Service(
            "scenario",
            http("POST", "/api/scenario", port=PORT),
            graph=scenario_flow,
            description="POST {client_id, scenario, params?, scope?}: a life event or a stress test, with two options.",
        ),
        Service(
            "scenario_combine",
            http("POST", "/api/scenario/combine", port=PORT),
            graph=combine_flow,
            description="POST {client_id, scenarios, params?, scope?, goals?}: stress tests together, no double count.",
        ),
        Service(
            "goals",
            http("POST", "/api/goals", port=PORT),
            graph=goals_flow,
            description="POST {client_id, scope?}: every life goal, with its gap, status and actions.",
        ),
        Service(
            "propose",
            http("POST", "/api/review/propose", port=PORT),
            graph=propose_flow,
            description="POST {client_id, scenario, title, option}: an option sent to the RM queue.",
        ),
        Service(
            "decide",
            http("POST", "/api/review/decide", port=PORT),
            graph=review_flow,
            description="POST {item_id, decision: approved|rejected, note?}: the RM's decision.",
        ),
        Service(
            "recommend",
            http("POST", "/api/review/recommend", port=PORT),
            graph=recommend_flow,
            description="POST {client_id, title, actions, note?, by}: the RM writes an action recommendation for a "
            "family; it reaches the client at once (the RM's alone, OWN-FB-18).",
        ),
        Service(
            "news_fetch",
            http("POST", "/api/news/ingest", port=PORT),
            graph=ingest_flow,
            description="POST {}: fetch every white-listed feed now, through the gates, into the inbox.",
        ),
        Service(
            "news_dismiss",
            http("POST", "/api/news/dismiss", port=PORT),
            graph=dismiss_flow,
            description="POST {ids, by?, note?}: the CIO drops items from the inbox.",
        ),
        Service(
            "news_release",
            http("POST", "/api/news/release", port=PORT),
            graph=release_flow,
            description="POST {item_id, by, note}: a CIO releases an item held by the restricted list.",
        ),
        Service(
            "event",
            http("POST", "/api/events", port=PORT),
            graph=event_flow,
            description="POST {news_ids, title?, by}: the CIO groups news into an event.",
        ),
        Service(
            "event_urgent",
            http("POST", "/api/events/urgent", port=PORT),
            graph=event_urgent_flow,
            description="POST {event_id, urgent, reason, by}: the CIO flags an event urgent, or takes the flag off "
            "(KPI-01).",
        ),
        Service(
            "cio_agent",
            http("POST", "/api/events/run-agent", port=PORT),
            graph=agent_queue_flow,
            description="POST {event_id, by, mode?: live|mock}: the CIO agent queued; the agent_worker job runs it.",
        ),
        Service(
            "view_decide",
            http("POST", "/api/views/decide", port=PORT),
            graph=decide_flow,
            description="POST {view_id, action, by, reason, idem_key?, edits?, responses?}: one CIO action.",
        ),
        Service(
            "run_recompute",
            http("POST", "/api/runs/recompute", port=PORT),
            graph=recompute_flow,
            description="POST {run_id, by, idem_key?}: re-apply the run's view on today's data and compare.",
        ),
        Service(
            "run_decide",
            http("POST", "/api/runs/decide", port=PORT),
            graph=run_decide_flow,
            description="POST {run_id, action: make_effective|withdraw, by, reason}: the CIO on a run.",
        ),
        Service(
            "research_upload",
            http("POST", "/api/research", port=PORT),
            graph=research_upload_flow,
            description="POST {item: {kind, report_no, title, summary, release_at, conflicts?, regulation?}, by}.",
        ),
        Service(
            "research_release",
            http("POST", "/api/research/release", port=PORT),
            graph=research_release_flow,
            description=(
                "POST {item_id, decision: release|reject, by, note}: a CIO other than the one who filed it, after the "
                "release time."
            ),
        ),
        Service(
            "goal_outflow",
            http("POST", "/api/goals/outflow", port=PORT),
            graph=goal_outflow_flow,
            description="POST {family_id, goal_id, purpose, country?, by}: the RM declares a goal's outflow.",
        ),
        Service(
            "model_estimate",
            http("POST", "/api/model/estimate", port=PORT),
            graph=model_estimate_flow,
            description="POST {by, end?, note?}: a CIO proposes the model estimated from market history (F2).",
        ),
        # last: it is mounted at "/", and would answer every path the services above own
        Service(
            "market_load_ask",
            http("POST", "/api/market/load", port=PORT),
            graph=market_load_ask_flow,
            description="POST {by, since}: an Admin queues a load of the market history (the market_load job runs it).",
        ),
        Service(
            "newsletter_draft",
            http("POST", "/api/newsletters", port=PORT),
            graph=newsletter_draft_flow,
            description="POST {view_ids, by, title?, mode?: template|agent, distribution?, conflict?}: a CIO drafts.",
        ),
        Service(
            "newsletter_act",
            http("POST", "/api/newsletters/act", port=PORT),
            graph=newsletter_act_flow,
            description="POST {newsletter_id, action: edit|submit|approve|return|withdraw, by, note?, changes?}.",
        ),
        Service(
            "policy_add",
            http("POST", "/api/policy", port=PORT),
            graph=policy_add_flow,
            description="POST {item: {gazette_url} | {source_url, title, number?, issued?, text?, status}, by}.",
        ),
        Service(
            "policy_verify",
            http("POST", "/api/policy/verify", port=PORT),
            graph=policy_verify_flow,
            description="POST {document_id, by, note}: a second CIO confirms the source (FR-306).",
        ),
        Service(
            "policy_status",
            http("POST", "/api/policy/status", port=PORT),
            graph=policy_status_flow,
            description="POST {document_id, status, by, note, date?}: where the document stands (the radar).",
        ),
        Service(
            "policy_summarise",
            http("POST", "/api/policy/summarise", port=PORT),
            graph=policy_summarise_flow,
            description="POST {document_id, by, mode?}: the policy agent on a verified document (FR-306).",
        ),
        Service(
            "alert_ack",
            http("POST", "/api/system/alerts/ack", port=PORT),
            graph=alert_ack_flow,
            description="POST {alert_id, by, note?}: “Đã xem” on an alert, by a role it is for (NFR-12).",
        ),
        Service(
            "account_request",
            http("POST", "/api/accounts/request", port=PORT),
            graph=account_request_flow,
            description="POST {kind: add|role|disable|enable|reset, by, person_id?, full_name?, email?, role?, title?, "
            "note?}: one Admin asks for a change to a staff account (Q-25); another Admin decides.",
        ),
        Service(
            "account_decide",
            http("POST", "/api/accounts/decide", port=PORT),
            graph=account_decide_flow,
            description="POST {request_id, action: approve|reject|withdraw, by, note?}: a second Admin approves or "
            "rejects (a reason), the proposer withdraws; an approved add or reset answers a one-time code once.",
        ),
        Service(
            "job_run",
            http("POST", "/api/jobs/run", port=PORT),
            graph=job_run_flow,
            description="POST {job, by}: Admin runs a background job now (control/jobs.py RUNNABLE); one at a time.",
        ),
        Service("web", asgi("/", port=PORT), app=web.app, description="The UI and the sample clients."),
    ],
    jobs=[
        # every client's alerts again: at 07:00 daily, before the RMs start (inside `operonx serve`),
        # and on demand with `operonx run policy_sweep`
        Job(
            "policy_sweep",
            graph=alerts_flow,
            items=every_client,
            key="client_id",
            schedule=schedule(at="07:00", port=PORT),
            description="07:00 daily: the policy sweep over every client.",
        ),
        # the assistant's retention (A4): conversations past the CIO's assistant_retention, expired memory items
        Job(
            "assistant_retention",
            graph=assistant_retention_flow,
            schedule=schedule(at="02:30", port=PORT),
            description="02:30 daily: the assistant's conversations past retention and expired memory items deleted.",
        ),
        # the memory consolidator (A6, ADR-0031): idle conversations into long-term items, ≤ 8,000 tokens each
        Job(
            "assistant_consolidate",
            graph=assistant_consolidate_flow,
            schedule=schedule(every="5m", port=PORT),
            timeout=600,
            description="Every 5 minutes: conversations idle 15 minutes distilled into the person's memory (A6).",
        ),
        # the news: every white-listed feed through the gates into the CIO's inbox, every 10 minutes
        # (inside `operonx serve`), and on demand with `operonx run news_ingest`; then the topic follow-ups (A6)
        Job(
            "news_ingest",
            graph=ingest_flow,
            schedule=schedule(every="10m", port=PORT),
            description="Every 10 minutes: the white-listed RSS feeds into the inbox (FR-101).",
        ),
        # important news collected (KPI-02, news/reference.py): the independent reference every 2 hours
        Job(
            "news_reference",
            graph=reference_flow,
            schedule=schedule(every="2h", port=PORT),
            timeout=120,
            description="Every 2 hours: Google News' business stories kept; a day later, each important one judged "
            "collected or not (KPI-02).",
        ),
        # the market data (F1, data/market_sources.json): each public source on its own clock into SQLite,
        # the cadence from its rate limit and when its data changes; `operonx run market_<kind>` runs one now
        Job(
            "market_equity",
            graph=market_equity_flow,
            schedule=schedule(at="15:45", port=PORT),
            timeout=600,
            description="15:45 daily: VN-Index and the stocks' closes (VNDirect, then Vietcap).",
        ),
        Job(
            "market_flows",
            graph=market_flows_flow,
            schedule=schedule(at="16:00", port=PORT),
            timeout=600,
            description="16:00 daily: foreign net buying on HOSE (cafef).",
        ),
        Job(
            "market_yields",
            graph=market_yields_flow,
            schedule=schedule(at="17:30", port=PORT),
            timeout=600,
            description="17:30 daily: government bond yields (HNX curve, then worldgovernmentbonds).",
        ),
        Job(
            "market_fx",
            graph=market_fx_flow,
            schedule=schedule(every="1h", port=PORT),
            timeout=300,
            description="Hourly: USD/VND (Vietcombank, then MSN).",
        ),
        Job(
            "market_world",
            graph=market_world_flow,
            schedule=schedule(every="1h", port=PORT),
            timeout=300,
            description="Hourly: gold, Brent, ACWI, S&P 500, US 10-year, the DXY's currencies (MSN).",
        ),
        Job(
            "market_crypto",
            graph=market_crypto_flow,
            schedule=schedule(every="1h", port=PORT),
            timeout=300,
            description="Hourly: Bitcoin and Ether (Binance).",
        ),
        Job(
            "market_gold",
            graph=market_gold_flow,
            schedule=schedule(every="1h", port=PORT),
            timeout=300,
            description="Hourly: SJC gold bars (PNJ's history).",
        ),
        Job(
            "market_load",
            graph=market_load_flow,
            schedule=schedule(every="1m", port=PORT),
            timeout=7200,
            keep_runs=200,
            description="Every minute: the market history load an Admin asked for in Hệ thống, if any.",
        ),
        Job(
            "agent_worker",
            graph=agent_worker_flow,
            schedule=schedule(every="5s", port=PORT),
            timeout=1800,
            keep_runs=500,
            description="Every 5 seconds: the oldest queued CIO agent run (AI-13), one at a time.",
        ),
        Job(
            "inbox_import",
            graph=inbox_import_flow,
            schedule=schedule(every="10m", port=PORT),
            timeout=1800,
            description="Every 10 minutes: the AI zone's packages through the same checks, imported or rejected.",
        ),
        Job(
            "zone_sync",
            graph=zone_sync_flow,
            schedule=schedule(every="10m", port=PORT),
            timeout=300,
            description="Every 10 minutes in inbox mode: the approved catalogues and released research to the AI zone.",
        ),
        Job(
            "audit_check",
            graph=audit_check_flow,
            schedule=schedule(every="1h", port=PORT),
            timeout=600,
            description="Hourly: the audit chain walked and new rows copied to write-once segments; an alert for "
            "the CIO and Admin when either is broken.",
        ),
        Job(
            "heartbeat",
            graph=heartbeat_flow,
            schedule=schedule(every="20s", port=PORT),
            timeout=30,
            keep_runs=200,
            description="Every 20 seconds: this minute recorded as up; availability in business hours against "
            "99.5 %, an alert for Admin below it (NFR-03).",
        ),
        Job(
            "agent_eval",
            graph=agent_eval_flow,
            schedule=schedule(every="1m", port=PORT),
            timeout=3600,
            keep_runs=200,
            description="Every minute: the fixed eval set on prompt and model proposals waiting for it (MEAS-07).",
        ),
        Job(
            "accuracy_score",
            graph=accuracy_flow,
            schedule=schedule(at="18:30", port=PORT),
            timeout=600,
            description="18:30 daily, after the market jobs: approved views' forecasts kept and scored (FEAT-18).",
        ),
        # the news agents' trial (BUSINESS_FEEDBACK_1021_PLAN B1, src/trial): the agents on their own each morning,
        # nothing approved; their drafts' shadow forecasts kept and scored, the report in out/trial/<day>.json
        Job(
            "trial_daily",
            graph=trial_daily_flow,
            schedule=schedule(at="08:30", port=PORT),
            timeout=3600,
            description="08:30 daily until MF_TRIAL_UNTIL: the news since the last run grouped into events by the CIO "
            "model, the CIO agent and the challenger on each, as agent:trial (B1.1).",
        ),
        Job(
            "trial_score",
            graph=trial_score_flow,
            schedule=schedule(every="15m", port=PORT),
            timeout=600,
            description="Every 15 minutes: the trial's drafts' shadow forecasts kept, the due ones scored, the report "
            "written (B1.2-B1.6).",
        ),
        # history on demand: `operonx run market_backfill [--set since=2020-01-01]`
        Job(
            "market_backfill",
            graph=market_backfill_flow,
            timeout=7200,
            description="On demand: every series' history from 2020-01 (dated sources weekly).",
        ),
        # how well statements are read: `operonx run statement_reading` (exit code: the gate's).
        # The three demo samples must pass; the free-text note needs a model (MF_AI=on).
        Eval(
            "statement_reading",
            graph=sample_flow,
            input="filename",
            dataset="dataset:statements",
            evaluators=[items_match],
            gate=Gate(threshold=0.8),
        ),
    ],
)

# Hệ thống lists the jobs as declared here (app/web.py cannot import this module); Việc nền runs them (control/jobs.py)
control_jobs.register(APP.jobs)
web.JOBS[:] = [
    {"id": j.name, "description": j.description, "when": (j.schedule.options if j.schedule else {})} for j in APP.jobs
]

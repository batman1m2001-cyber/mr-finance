"""Mr. Finance: the whole picture of a client's wealth, and what is moving it.

POST /api/dashboard {client_id, scope?, months?} ──► dashboard_flow ──► the dashboard
POST /api/flows     {client_id, scope?, month?} ──► flows_flow ──► a month's money in → out, with the rows
POST /api/feed      {client_id, scope?, role?} ──► feed_flow ──► what matters now, why, and its evidence
POST /api/copilot   {question, role, client_id?, scope?, route?, confirm?} ──► copilot_flow ──► a templated answer
POST /api/config/propose, /api/config/decide ──► versioned configuration, propose then approve (FR-701)
POST /api/statement {client_id, filename, content} ──► statement_flow ──► holdings read (AI or rules)
POST /api/declare   {client_id, message, session_id} ──► declare_flow ──► the chat's reply, what it recorded
POST /api/risk      {client_id, answers} ──► risk_flow ──► the next question, or the profile
POST /api/alerts    {client_id, scope?} ──► alerts_flow ──► policies, macro, infrastructure, in VND
POST /api/scenario  {client_id, scenario, params?} ──► scenario_flow ──► numbers, a light and a heavy option
POST /api/goals     {client_id, scope?} ──► goals_flow ──► every life goal: need, have, gap, status, actions
POST /api/review/propose ──► propose_flow (the RM queue) · POST /api/review/decide ──► review_flow
07:00 daily, and `operonx run policy_sweep` ──► the policy_sweep job: alerts_flow for every client
every 10 min, POST /api/news/ingest, `operonx run news_ingest` ──► ingest_flow: the feeds into the inbox
15:45/16:00/17:30 daily and hourly, `operonx run market_<kind>` ──► the market jobs: public sources into SQLite
     (market_backfill on demand) · GET /api/market[/series] ──► app/web.py (the source registry, the series)
POST /api/news/dismiss ──► dismiss_flow · POST /api/news/release ──► release_flow (Compliance)
GET  /api/news/inbox ──► app/web.py (the inbox and the feed-health strip)
POST /api/events ──► event_flow · POST /api/events/run-agent ──► cio_agent_flow (agent + challenger)
POST /api/views/decide ──► decide_flow · GET /api/events[/{id}], /api/views/{id}, /api/agents ──► app/web.py
approve ──► an application run for every family · POST /api/runs/recompute, /api/runs/decide ──► recompute_flow,
     run_decide_flow · GET /api/runs[/{id}[/verify]], /api/families/{id}/impact?role=, /api/trace/{run}/{family},
     /api/rm/today, /api/audit[/verify] ──► app/web.py
POST /api/research, /api/research/release, /api/goals/outflow ──► the research and goal-branch flows ·
     GET /api/research, /api/goals/regulation ──► app/web.py
GET  /api/clients, /api/advisory[/all], /api/views, POST /api/reset, GET / ──► app/web.py (the sample
     clients, the specialist team, the advisory track record, the house views, the UI)

Each service runs its graph as is: the JSON body fills the graph's parameters, and the reply is
its outputs (`{"dashboard": ...}`, `{"read": ...}`, ...). Every service and job of the product is
declared here; operonx.toml only points at `APP`.
"""

from operonx.app import Application, Eval, Service, asgi, env, http, schedule
from operonx.app.evals import Gate
from operonx.app.jobs import Job

from app import web
from apply.graph import recompute_flow, run_decide_flow
from control.graph import config_decide_flow, config_propose_flow
from copilot.graph import copilot_flow
from dashboard.graph import dashboard_flow
from declare.graph import declare_flow
from events.graph import event_flow
from feed.graph import feed_flow
from flows.graph import flows_flow
from impact.graph import alerts_flow
from impact.ops import every_client
from market.graph import (
    market_backfill_flow,
    market_crypto_flow,
    market_equity_flow,
    market_flows_flow,
    market_fx_flow,
    market_gold_flow,
    market_world_flow,
    market_yields_flow,
    model_estimate_flow,
)
from measure.graph import accuracy_flow
from news.graph import dismiss_flow, ingest_flow, release_flow
from overview.graph import overview_flow
from research.graph import goal_outflow_flow, research_release_flow, research_upload_flow
from review.graph import propose_flow, review_flow
from risk.graph import risk_flow
from scenarios.graph import goals_flow, scenario_flow
from search.graph import search_flow
from statements.checks import items_match
from statements.graph import sample_flow, statement_flow
from views.graph import cio_agent_flow, decide_flow

PORT = env("PORT", 8030)

APP = Application(
    "mr-finance",
    description="Consolidate every asset a client holds, anywhere, into one picture — and say what is moving it.",
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
            description="POST {item_id, by, note}: Compliance releases an item held by the restricted list.",
        ),
        Service(
            "event",
            http("POST", "/api/events", port=PORT),
            graph=event_flow,
            description="POST {news_ids, title?, by}: the CIO groups news into an event.",
        ),
        Service(
            "cio_agent",
            http("POST", "/api/events/run-agent", port=PORT),
            graph=cio_agent_flow,
            description="POST {event_id, by, mode?: live|mock}: the CIO agent, then the challenger.",
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
            description="POST {item_id, decision: release|reject, by, note}: Compliance, after the release time.",
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
        # the news: every white-listed feed through the gates into the CIO's inbox, every 10 minutes
        # (inside `operonx serve`), and on demand with `operonx run news_ingest`
        Job(
            "news_ingest",
            graph=ingest_flow,
            schedule=schedule(every="10m", port=PORT),
            description="Every 10 minutes: the white-listed RSS feeds into the inbox (FR-101).",
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
            "accuracy_score",
            graph=accuracy_flow,
            schedule=schedule(at="18:30", port=PORT),
            timeout=600,
            description="18:30 daily, after the market jobs: approved views' forecasts kept and scored (FEAT-18).",
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

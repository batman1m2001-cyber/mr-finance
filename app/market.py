"""The market jobs: public sources into SQLite on their own clocks, backfill, the agent eval, accuracy, the trial.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from operonx.app.jobs import Job

from app.serve import PORT, schedule
from market.graph import market_flow

JOBS = [
    # the market data (F1, data/market_sources.json): each public source on its own clock into SQLite,
    # the cadence from its rate limit and when its data changes; `operonx run market_<kind>` runs one now
    Job(
        "market_equity",
        graph=market_flow,
        inputs={"action": "pull", "job": "market_equity"},
        schedule=schedule(at="15:45", port=PORT),
        timeout=600,
        description="15:45 daily: VN-Index and the stocks' closes (VNDirect, then Vietcap).",
    ),
    Job(
        "market_flows",
        graph=market_flow,
        inputs={"action": "pull", "job": "market_flows"},
        schedule=schedule(at="16:00", port=PORT),
        timeout=600,
        description="16:00 daily: foreign net buying on HOSE (cafef).",
    ),
    Job(
        "market_yields",
        graph=market_flow,
        inputs={"action": "pull", "job": "market_yields"},
        schedule=schedule(at="17:30", port=PORT),
        timeout=600,
        description="17:30 daily: government bond yields (HNX curve, then worldgovernmentbonds).",
    ),
    Job(
        "market_fx",
        graph=market_flow,
        inputs={"action": "pull", "job": "market_fx"},
        schedule=schedule(every="1h", port=PORT),
        timeout=300,
        description="Hourly: USD/VND (Vietcombank, then MSN).",
    ),
    Job(
        "market_world",
        graph=market_flow,
        inputs={"action": "pull", "job": "market_world"},
        schedule=schedule(every="1h", port=PORT),
        timeout=300,
        description="Hourly: gold, Brent, ACWI, S&P 500, US 10-year, the DXY's currencies (MSN).",
    ),
    Job(
        "market_crypto",
        graph=market_flow,
        inputs={"action": "pull", "job": "market_crypto"},
        schedule=schedule(every="1h", port=PORT),
        timeout=300,
        description="Hourly: Bitcoin and Ether (Binance).",
    ),
    Job(
        "market_gold",
        graph=market_flow,
        inputs={"action": "pull", "job": "market_gold"},
        schedule=schedule(every="1h", port=PORT),
        timeout=300,
        description="Hourly: SJC gold bars (PNJ's history).",
    ),
    Job(
        "market_load",
        graph=market_flow,
        inputs={"action": "load"},
        schedule=schedule(every="1m", port=PORT),
        timeout=7200,
        keep_runs=200,
        description="Every minute: the market history load an Admin asked for in Hệ thống, if any.",
    ),
    Job(
        "agent_eval",
        graph=market_flow,
        inputs={"action": "agent_eval"},
        schedule=schedule(every="1m", port=PORT),
        timeout=3600,
        keep_runs=200,
        description="Every minute: the fixed eval set on prompt and model proposals waiting for it (MEAS-07).",
    ),
    Job(
        "accuracy_score",
        graph=market_flow,
        inputs={"action": "accuracy"},
        schedule=schedule(at="18:30", port=PORT),
        timeout=600,
        description="18:30 daily, after the market jobs: approved views' forecasts kept and scored (FEAT-18).",
    ),
    # the news agents' trial (BUSINESS_FEEDBACK_1021_PLAN B1, src/trial): the agents on their own each morning,
    # nothing approved; their drafts' shadow forecasts kept and scored, the report in out/trial/<day>.json
    Job(
        "trial_daily",
        graph=market_flow,
        inputs={"action": "trial_daily"},
        schedule=schedule(at="08:30", port=PORT),
        timeout=3600,
        description="08:30 daily until MF_TRIAL_UNTIL: the news since the last run grouped into events by the CIO "
        "model, the CIO agent and the challenger on each, as agent:trial (B1.1).",
    ),
    Job(
        "trial_score",
        graph=market_flow,
        inputs={"action": "trial_score"},
        schedule=schedule(every="15m", port=PORT),
        timeout=600,
        description="Every 15 minutes: the trial's drafts' shadow forecasts kept, the due ones scored, the report "
        "written (B1.2-B1.6).",
    ),
    # history on demand: `operonx run market_backfill [--set since=2020-01-01]`
    Job(
        "market_backfill",
        graph=market_flow,
        inputs={"action": "backfill", "since": "2020-01-01"},
        timeout=7200,
        description="On demand: every series' history from 2020-01 (dated sources weekly).",
    ),
]

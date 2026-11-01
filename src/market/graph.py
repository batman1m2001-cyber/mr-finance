"""The market and measurement jobs' one graph (app/main.py gives each job its `action`, and `job` for a source;
`operonx run market_<kind>` or `operonx run accuracy_score` runs one now). The Admin's two requests are
control/graph.py admin_flow."""

from operonx import END, START, graph
from operonx.core.ops import if_

from assistant.ops import follow_ups_market
from market.ops import backfill, pull, run_loads
from measure.ops import score_forecasts
from trial.ops import trial_day, trial_score
from views.ops import run_evals


@graph
def market_flow(action="pull", job=None, since=None, only=None, force=False, today=None, tick=None, at=None):
    """``pull``: one source's series (``job``), then the follow-ups on them (A6) · ``backfill``: every series'
    history from ``since`` · ``load``: the history load an Admin asked for, if any · ``accuracy``: record and score
    the approved views' forecasts · ``trial_daily``: the news since the last run into events, the agents on each,
    their shadow forecasts kept · ``trial_score``: the trial's forecasts kept and scored, its report written ·
    ``agent_eval``: the eval set on pending prompt and model proposals."""
    got = pull(job=job, since=since, only=only)
    checked = follow_ups_market(job=job, after=got["run"])  # the follow-ups on its series (A6)
    filled = backfill(since=since, only=only)
    loaded = run_loads(tick=tick, at=at)
    accuracy = score_forecasts(today=today)
    daily = trial_day(force=force, tick=tick, at=at)
    scored = trial_score(today=today, tick=tick, at=at)
    evals = run_evals(tick=tick, at=at)
    START >> if_(action == "pull", got).if_(action == "backfill", filled).if_(action == "accuracy", accuracy).if_(
        action == "trial_daily", daily
    ).if_(action == "trial_score", scored).if_(action == "agent_eval", evals).else_(loaded)
    got >> checked >> END
    got >> END  # the run stays the graph's answer
    filled >> END
    loaded >> END
    accuracy >> END
    daily >> END
    scored >> END
    evals >> END

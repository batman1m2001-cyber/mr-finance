"""The market jobs' one graph (app/main.py gives each job its `action` and `job`; `operonx run market_<kind>` runs
one now). The Admin's two requests are control/graph.py admin_flow."""

from operonx import END, START, graph
from operonx.core.ops import if_

from assistant.ops import follow_ups_market
from market.ops import backfill, pull, run_loads


@graph
def market_flow(action="pull", job=None, since=None, only=None, tick=None, at=None):
    """``pull``: one source's series (``job``), then the follow-ups on them (A6) · ``backfill``: every series'
    history from ``since`` · ``load``: the history load an Admin asked for, if any."""
    got = pull(job=job, since=since, only=only)
    checked = follow_ups_market(job=job, after=got["run"])  # the follow-ups on its series (A6)
    filled = backfill(since=since, only=only)
    loaded = run_loads(tick=tick, at=at)
    START >> if_(action == "pull", got).if_(action == "backfill", filled).else_(loaded)
    got >> checked >> END
    got >> END  # the run stays the graph's answer
    filled >> END
    loaded >> END

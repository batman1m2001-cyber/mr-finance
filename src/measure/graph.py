"""The daily accuracy job (app/main.py schedules it; `operonx run accuracy_score` runs it now)."""

from operonx import END, START, graph

from measure.ops import score_forecasts


@graph
def accuracy_flow(today=None, tick=None, at=None):
    """Record and score the approved views' forecasts."""
    done = score_forecasts(today=today)
    START >> done >> END

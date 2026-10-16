"""recompute_flow (FR-405) and run_decide_flow: served on POST /api/runs/recompute and
POST /api/runs/decide. A view's first run is made by its approval (views.ops.decide_view).

The run is the parameter ``run``: ``run_id`` is a name operonx's doors read themselves (a durable run's id)."""

from operonx import END, START, graph

from apply.ops import decide_run, recompute


@graph
def recompute_flow(run, by="cio", idem_key=None):
    """Re-apply the run's view on today's data and compare."""
    done = recompute(run_id=run, by=by, idem_key=idem_key)
    START >> done >> END


@graph
def run_decide_flow(run, action, by, reason=""):
    """The CIO makes a held run effective, or withdraws a run."""
    done = decide_run(run_id=run, action=action, by=by, reason=reason)
    START >> done >> END

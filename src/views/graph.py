"""cio_agent_flow: an event → four analyst groups at once (and any the prompts configuration adds) →
debate → synthesis and format check → the view kept → the challenger (BRD FR-301…303, §8.1). The CIO's action on a view is review_flow (review/graph.py). (The fixed eval set on prompt and model proposals, MEAS-07, runs in measure/graph.py evaluation_flow.)

Served as is: POST /api/events/run-agent queues a run in news/graph.py news_flow."""

from operonx import END, START, graph

from views.ops import analyse, analyse_more, compose, discuss, gather, review, save_view
from views.worker import work_queue


@graph
def cio_agent_flow(event_id, by="cio", mode=None):
    """The CIO agent on one event; the result is the view, its findings and the approval checks."""
    got = gather(event_id=event_id, by=by, mode=mode)
    macro = analyse(lens="macro", packet=got["packet"], mode=got["mode"], run_id=got["run_id"])
    equity = analyse(lens="equity", packet=got["packet"], mode=got["mode"], run_id=got["run_id"])
    credit = analyse(lens="credit", packet=got["packet"], mode=got["mode"], run_id=got["run_id"])
    other = analyse(lens="other", packet=got["packet"], mode=got["mode"], run_id=got["run_id"])
    more = analyse_more(packet=got["packet"], mode=got["mode"], run_id=got["run_id"])
    talk = discuss(
        packet=got["packet"],
        mode=got["mode"],
        run_id=got["run_id"],
        macro=macro["note"],
        equity=equity["note"],
        credit=credit["note"],
        other=other["note"],
        macro_error=macro["error"],
        equity_error=equity["error"],
        credit_error=credit["error"],
        other_error=other["error"],
        more=more["notes"],
        more_error=more["error"],
    )
    made = compose(
        packet=got["packet"],
        notes=talk["notes"],
        merged=talk["merged"],
        mode=got["mode"],
        run_id=got["run_id"],
        error=talk["error"],
    )
    kept = save_view(view_id=got["view_id"], run_id=got["run_id"], view=made["view"], errors=made["errors"], by=by)
    checked = review(view_id=kept["view_id"], ok=kept["ok"], by=by)
    START >> got
    got >> macro
    got >> equity
    got >> credit
    got >> other
    got >> more
    more >> talk
    macro >> talk
    equity >> talk
    credit >> talk
    other >> talk
    talk >> made >> kept >> checked >> END


@graph
def agent_worker_flow(tick=None, at=None):
    """The ``agent_worker`` job (every 5 seconds): the oldest queued run."""
    done = work_queue(tick=tick, at=at)
    START >> done >> END

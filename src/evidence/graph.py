"""evidence_flow: one flow for the evidence feature, a route picks its `action` (app/main.py binds it with `variants`,
and `bodies.py` is each route's request contract).

read          POST /api/evidence               the frames behind the alerts' evidence, as the caller's role may read them
decide        POST /api/evidence/decide        the CIO approves, returns or rejects a frame
draft         POST /api/evidence/draft         the evidence agent drafts one news item's frame for the CIO
draft_decide  POST /api/evidence/draft/decide  the CIO approves, returns or rejects the agent's draft
type          POST /api/evidence/type          the CIO adds an event type, or precedent dates to one (P2)"""

from operonx import END, START, graph
from operonx.core.ops import if_

from evidence.ops import decide, decide_draft, draft, read, save_type
from wealth.action import route


@graph
def evidence_flow(
    action="read",
    factor=None,
    role=None,
    decision=None,
    by=None,
    note="",
    news_id=None,
    mode="",
    event_type=None,
    label=None,
    dates=None,
    series=None,
):
    """Each news item's evidence: the statistics or the qualitative frame, as the caller's role may read it; or the
    CIO's and the agent's writes on it."""
    which = route(action=action)
    decided = decide(factor=factor, decision=decision, by=by, note=note)
    drafted = draft(news_id=news_id, by=by, mode=mode)
    draft_decided = decide_draft(news_id=news_id, decision=decision, by=by, note=note)
    typed = save_type(event_type=event_type, label=label, dates=dates, series=series, by=by)
    shown = read(factor=factor, role=role)
    a = which["action"]
    START >> which >> if_(a == "decide", decided).if_(a == "draft", drafted).if_(a == "draft_decide", draft_decided).if_(
        a == "type", typed
    ).else_(shown)
    decided >> END
    drafted >> END
    draft_decided >> END
    typed >> END
    shown >> END

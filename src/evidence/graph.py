"""evidence_flow: the frames behind the alerts' evidence; evidence_decide_flow: the CIO's review of one.

evidence_draft_flow: the agent's draft for one news item; evidence_draft_decide_flow: the CIO's review of it.

evidence_type_flow: the CIO adds an event type, or precedent dates to one (P2).

Served on POST /api/evidence, /api/evidence/decide, /api/evidence/draft, /api/evidence/draft/decide and
/api/evidence/type (app/main.py)."""

from operonx import END, START, graph

from evidence.ops import decide, decide_draft, draft, read, save_type


@graph
def evidence_flow(factor=None, role=None):
    """Each news item's evidence: the statistics or the qualitative frame, as the caller's role may read it."""
    out = read(factor=factor, role=role)
    START >> out >> END


@graph
def evidence_decide_flow(factor=None, decision=None, by=None, note=""):
    """The CIO approves, returns or rejects a frame."""
    out = decide(factor=factor, decision=decision, by=by, note=note)
    START >> out >> END


@graph
def evidence_draft_flow(news_id=None, by=None, mode=""):
    """The evidence agent reads one news item and drafts its frame for the CIO."""
    out = draft(news_id=news_id, by=by, mode=mode)
    START >> out >> END


@graph
def evidence_draft_decide_flow(news_id=None, decision=None, by=None, note=""):
    """The CIO approves, returns or rejects the agent's draft."""
    out = decide_draft(news_id=news_id, decision=decision, by=by, note=note)
    START >> out >> END


@graph
def evidence_type_flow(event_type=None, label=None, dates=None, series=None, by=None):
    """The CIO adds an event type to the catalogue, or precedent dates to one."""
    out = save_type(event_type=event_type, label=label, dates=dates, series=series, by=by)
    START >> out >> END

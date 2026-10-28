"""evidence_flow: the frames behind the alerts' evidence; evidence_decide_flow: the CIO's review of one.

evidence_draft_flow: the agent's draft for one news item; evidence_draft_decide_flow: the CIO's review of it.

Served on POST /api/evidence, /api/evidence/decide, /api/evidence/draft and /api/evidence/draft/decide (app/main.py)."""

from operonx import END, START, graph

from evidence.ops import decide, decide_draft, draft, read


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

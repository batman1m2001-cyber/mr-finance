"""event_flow: news items the CIO picked → one event (FR-103). Served on POST /api/events. event_urgent_flow: the
CIO's urgent flag (BRD-KPI-01), on POST /api/events/urgent."""

from operonx import END, START, graph

from events.ops import flag_urgent, group


@graph
def event_flow(news_ids, title=None, by="cio"):
    """Group news into an event; it is held while any item waits for Compliance (FR-105)."""
    made = group(news_ids=news_ids, title=title, by=by)
    START >> made >> END


@graph
def event_urgent_flow(event_id, urgent=True, reason="", by="cio"):
    """The CIO flags an event urgent (with a reason) or takes the flag off."""
    done = flag_urgent(event_id=event_id, urgent=urgent, reason=reason, by=by)
    START >> done >> END

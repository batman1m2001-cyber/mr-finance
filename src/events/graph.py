"""event_flow: news items the CIO picked → one event (FR-103). Served on POST /api/events."""

from operonx import END, START, graph

from events.ops import group


@graph
def event_flow(news_ids, title=None, by="cio"):
    """Group news into an event; it is held while any item waits for Compliance (FR-105)."""
    made = group(news_ids=news_ids, title=title, by=by)
    START >> made >> END

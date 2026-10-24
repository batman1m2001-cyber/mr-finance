"""ingest_flow: every white-listed feed → the gates → sorted → kept (BRD FR-101…105).

Runs every 10 minutes inside `operonx serve` (the news_ingest job, app/main.py), on demand with
`operonx run news_ingest`, and on POST /api/news/ingest (the inbox's "Lấy tin ngay"). ``feeds``
replaces the network with given XML ({source id: text}); ``tick`` and ``at`` are what the schedule
sends and are not used."""

from operonx import END, START, graph

from assistant.ops import follow_ups_topics
from news.ops import dismiss, fetch, keep, reference_check, release, screen


@graph
def ingest_flow(feeds=None, now=None, tick=None, at=None):
    """Fetch, gate, sort and keep the news."""
    got = fetch(feeds=feeds, now=now)
    seen = screen(fetched=got["fetched"], at=got["at"])
    kept = keep(rows=seen["rows"], counts=seen["counts"], at=got["at"], started=got["started"])
    topics = follow_ups_topics(after=kept["ingest"])  # the follow-ups on approved events (A6)
    START >> got >> seen >> kept >> topics >> END
    kept >> END  # the ingest stays the graph's answer (POST /api/news/ingest)


@graph
def dismiss_flow(ids, by="cio", note=""):
    """The CIO drops items from the inbox (FR-103)."""
    done = dismiss(ids=ids, by=by, note=note)
    START >> done >> END


@graph
def release_flow(item_id, by, note):
    """Compliance lets an item that names someone on the restricted list through (BR-04)."""
    done = release(item_id=item_id, by=by, note=note)
    START >> done >> END


@graph
def reference_flow(feed=None, now=None, tick=None, at=None):
    """The independent reference read, its stories kept and judged (KPI-02)."""
    done = reference_check(feed=feed, now=now)
    START >> done >> END

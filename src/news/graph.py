"""news_flow: the news, its events and the alerts they cause, one flow; a route or a job picks its `action`
(app/main.py binds it with `variants` or `Job(inputs=...)`, and `bodies.py` is each route's request contract).

ingest     the news_ingest and zone_news jobs, POST /api/news/ingest: every white-listed feed → the gates → sorted →
           kept (BRD FR-101…105), then the follow-ups on approved events (A6). ``feeds`` replaces the network with
           given XML ({source id: text}); ``tick`` and ``at`` are what the schedule sends and are not used.
reference  the news_reference job: the independent reference read, its stories kept and judged (KPI-02)
dismiss    POST /api/news/dismiss: the CIO drops items from the inbox (FR-103)
release    POST /api/news/release: the CIO lets an item that names someone on the restricted list through (BR-04)
event      POST /api/events: news items the CIO picked → one event, held while any item waits for the CIO (FR-105)
urgent     POST /api/events/urgent: the CIO's urgent flag on an event (BRD-KPI-01)
queue      POST /api/events/run-agent: the CIO's agent run, queued for the ``agent_worker`` job (AI-13)
alerts     POST /api/alerts and the policy_sweep job (every client, 07:00): the client's holdings and profile → every
           factor scored → the alerts, kept"""

from operonx import END, START, graph
from operonx.core.ops import if_

from assistant.ops import follow_ups_topics
from consolidate.graph import consolidate_flow
from events.ops import flag_urgent, group
from impact.ops import check_request as check_alerts
from impact.ops import keep as keep_alerts
from impact.ops import profile_of, score
from news.ops import dismiss, fetch, keep, reference_check, release, screen
from views.worker import queue_agent


@graph
def news_flow(
    action="ingest",
    feeds=None,
    now=None,
    tick=None,
    at=None,
    feed=None,
    ids=None,
    by="cio",
    note="",
    item_id=None,
    news_ids=None,
    title=None,
    event_id=None,
    urgent=True,
    reason="",
    mode=None,
    client_id=None,
    scope="personal",
):
    """Fetch, gate, sort and keep the news; group it into events; what is moving a client's wealth."""
    got = fetch(feeds=feeds, now=now)
    seen = screen(fetched=got["fetched"], at=got["at"])
    kept = keep(rows=seen["rows"], counts=seen["counts"], at=got["at"], started=got["started"])
    topics = follow_ups_topics(after=kept["ingest"])  # the follow-ups on approved events (A6)
    referenced = reference_check(feed=feed, now=now)
    dismissed = dismiss(ids=ids, by=by, note=note)
    released = release(item_id=item_id, by=by, note=note)
    grouped = group(news_ids=news_ids, title=title, by=by)
    flagged = flag_urgent(event_id=event_id, urgent=urgent, reason=reason, by=by)
    queued = queue_agent(event_id=event_id, by=by, mode=mode)
    ask = check_alerts(client_id=client_id, scope=scope)
    held = consolidate_flow(client_id=ask["client_id"], scope=ask["scope"])
    who = profile_of(client_id=ask["client_id"], members=held["members"])
    found = score(holdings=held["holdings"], profile=who["profile"])
    alerts = keep_alerts(client_id=ask["client_id"], scope=ask["scope"], alerts=found["alerts"], net_worth=found["net_worth"])

    a = action
    START >> if_(a == "ingest", got).if_(a == "reference", referenced).if_(a == "dismiss", dismissed).if_(
        a == "release", released
    ).if_(a == "event", grouped).if_(a == "urgent", flagged).if_(a == "queue", queued).if_(a == "alerts", ask).build()
    got >> seen >> kept >> topics >> END
    kept >> END  # the ingest stays the answer of POST /api/news/ingest
    ask >> held >> who >> found >> alerts >> END
    referenced >> END
    dismissed >> END
    released >> END
    grouped >> END
    flagged >> END
    queued >> END

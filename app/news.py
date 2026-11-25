"""The news: alerts, the inbox, events, the CIO agent, and the ingest, reference, worker, inbox and zone jobs.

What this feature exposes: its SERVICES and JOBS, which app/main.py collects, and each route's
request contract (Service(body=...)): the fields it accepts, which are required, their defaults. The
contract functions are never called; the graph serves the route."""

from typing import Any, Dict, List, Optional

from operonx.app import Service, http
from operonx.app.jobs import Job

from app.serve import PORT, schedule
from impact.ops import every_client
from news.graph import news_flow


def ingest(feeds: Optional[Dict[str, Any]] = None, now: Any = None, tick: Any = None, at: Any = None): ...


def dismiss(ids: List[str], by: str = "cio", note: str = ""): ...


def release(item_id: str, by: str, note: str): ...


def event(news_ids: List[str], title: Optional[str] = None, by: str = "cio"): ...


def urgent(event_id: str, urgent: bool = True, reason: str = "", by: str = "cio"): ...


def queue(event_id: str, by: str = "cio", mode: Optional[str] = None): ...


def alerts(client_id: str, scope: str = "personal"): ...


SERVICES = [
    Service(
        "alerts",
        http("POST", "/api/alerts", port=PORT),
        graph=news_flow,
        variants={"alerts": {"action": "alerts"}},
        body=alerts,
        description="POST {client_id, scope?}: what is moving the client's wealth, in VND, with sources.",
    ),
    Service(
        "news_fetch",
        http("POST", "/api/news/ingest", port=PORT),
        graph=news_flow,
        variants={"ingest": {"action": "ingest"}},
        body=ingest,
        description="POST {}: fetch every white-listed feed now, through the gates, into the inbox.",
    ),
    Service(
        "news_dismiss",
        http("POST", "/api/news/dismiss", port=PORT),
        graph=news_flow,
        variants={"dismiss": {"action": "dismiss"}},
        body=dismiss,
        description="POST {ids, by?, note?}: the CIO drops items from the inbox.",
    ),
    Service(
        "news_release",
        http("POST", "/api/news/release", port=PORT),
        graph=news_flow,
        variants={"release": {"action": "release"}},
        body=release,
        description="POST {item_id, by, note}: a CIO releases an item held by the restricted list.",
    ),
    Service(
        "event",
        http("POST", "/api/events", port=PORT),
        graph=news_flow,
        variants={"event": {"action": "event"}},
        body=event,
        description="POST {news_ids, title?, by}: the CIO groups news into an event.",
    ),
    Service(
        "event_urgent",
        http("POST", "/api/events/urgent", port=PORT),
        graph=news_flow,
        variants={"urgent": {"action": "urgent"}},
        body=urgent,
        description="POST {event_id, urgent, reason, by}: the CIO flags an event urgent, or takes the flag off "
        "(KPI-01).",
    ),
    Service(
        "cio_agent",
        http("POST", "/api/events/run-agent", port=PORT),
        graph=news_flow,
        variants={"queue": {"action": "queue"}},
        body=queue,
        description="POST {event_id, by, mode?: live|mock}: the CIO agent queued; the agent_worker job runs it.",
    ),
]


JOBS = [
    # every client's alerts again: at 07:00 daily, before the RMs start (inside `operonx serve`),
    # and on demand with `operonx run policy_sweep`
    Job(
        "policy_sweep",
        graph=news_flow,
        inputs={"action": "alerts"},
        items=every_client,
        key="client_id",
        schedule=schedule(at="07:00", port=PORT),
        description="07:00 daily: the policy sweep over every client.",
    ),
    # the news: every white-listed feed through the gates into the CIO's inbox, every 10 minutes
    # (inside `operonx serve`), and on demand with `operonx run news_ingest`; then the topic follow-ups (A6)
    Job(
        "news_ingest",
        graph=news_flow,
        inputs={"action": "ingest"},
        schedule=schedule(every="10m", port=PORT),
        description="Every 10 minutes: the white-listed RSS feeds into the inbox (FR-101).",
    ),
    # important news collected (KPI-02, news/reference.py): the independent reference every 2 hours
    Job(
        "news_reference",
        graph=news_flow,
        inputs={"action": "reference"},
        schedule=schedule(every="2h", port=PORT),
        timeout=120,
        description="Every 2 hours: Google News' business stories kept; a day later, each important one judged "
        "collected or not (KPI-02).",
    ),
    Job(
        "agent_worker",
        graph=news_flow,
        inputs={"action": "worker"},
        schedule=schedule(every="5s", port=PORT),
        timeout=1800,
        keep_runs=500,
        description="Every 5 seconds: the oldest queued CIO agent run (AI-13), one at a time.",
    ),
    Job(
        "inbox_import",
        graph=news_flow,
        inputs={"action": "inbox"},
        schedule=schedule(every="10m", port=PORT),
        timeout=1800,
        description="Every 10 minutes: the AI zone's packages through the same checks, imported or rejected.",
    ),
    Job(
        "zone_sync",
        graph=news_flow,
        inputs={"action": "sync"},
        schedule=schedule(every="10m", port=PORT),
        timeout=300,
        description="Every 10 minutes in inbox mode: the approved catalogues and released research to the AI zone.",
    ),
]

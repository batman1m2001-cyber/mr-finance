"""The AI zone (BRD §5, ZONE-01…06; F-D7): a second process, served with `operonx serve -f operonx.zone.toml`, with its
own SQLite file (``MF_STATE``, e.g. data/zone.db) and its own data folder holding only the catalogues
(``MF_DATA``, made by scripts/make_zone_data.py). It reads no customer and no member of staff (``MF_ZONE=on`` makes
any such read raise).

every 10 min ──► zone_news: ingest_flow, the white-listed feeds into the zone's own news (TCB's sources, synced)
every 15 min ──► zone_agent: deliveries not yet taken, again; then one event under the day's cap
     (``MF_ZONE_DAILY``), cio_agent_flow on it, the package signed (``MF_INBOX_KEY``) to TCB's POST /api/inbox
     (``MF_TCB_INBOX``), reading back only an id
POST /api/zone/sync ◄── TCB's zone_sync job: the approved catalogues and released research (``MF_ZONE_KEY``)
GET  /api/zone/status ──► what the zone holds and what it sent
"""

import os

from operonx.app import Application, Service, asgi, env, schedule
from operonx.app.jobs import Job

os.environ["MF_ZONE"] = "on"  # before any read: this process is the zone

from news.graph import ingest_flow  # noqa: E402
from zone import web  # noqa: E402
from zone.graph import zone_agent_flow  # noqa: E402

PORT = env("ZONE_PORT", 8040)

APP = Application(
    "mr-finance-zone",
    description="The AI zone: public news, released research and approved catalogues in; signed views out.",
    services=[Service("zone", asgi("/", port=PORT), app=web.app, description="TCB's sync in; the zone's status.")],
    jobs=[
        Job(
            "zone_news",
            graph=ingest_flow,
            schedule=schedule(every="10m", port=PORT),
            description="Every 10 minutes: the white-listed feeds into the zone's own news.",
        ),
        Job(
            "zone_agent",
            graph=zone_agent_flow,
            schedule=schedule(every="15m", port=PORT),
            timeout=1800,
            description="Every 15 minutes: one event's view, under the day's cap, signed to TCB's inbox.",
        ),
    ],
)

"""Mr. Finance: the whole picture of a client's wealth, and what is moving it.

POST /api/dashboard {client_id, scope?, months?} ──► dashboard_flow ──► the dashboard
GET  /api/clients, POST /api/reset, GET /    ──► app/web.py (the sample clients, the UI)

Every service and job of the product is declared here; operonx.toml only points at `APP`.
"""

from operonx.app import Application, Service, asgi, env, http

from app import web
from dashboard.graph import dashboard_api

PORT = env("PORT", 8030)

APP = Application(
    "mr-finance",
    description="Consolidate every asset a client holds, anywhere, into one picture — and say "
    "what is moving it.",
    services=[
        Service(
            "dashboard",
            http("POST", "/api/dashboard", port=PORT),
            graph=dashboard_api,
            description="POST {client_id, scope: personal|family, months}: the dashboard.",
        ),
        # last: it is mounted at "/", and would answer every path the services above own
        Service(
            "web", asgi("/", port=PORT), app=web.app, description="The UI and the sample clients."
        ),
    ],
)

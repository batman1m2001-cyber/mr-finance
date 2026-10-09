"""Mr. Finance: the whole picture of a client's wealth, and what is moving it.

POST /api/dashboard {client_id, scope?, months?} ──► dashboard_flow ──► the dashboard
POST /api/statement {client_id, filename, content} ──► statement_flow ──► holdings read (AI or rules)
POST /api/declare   {client_id, message, session_id} ──► declare_flow ──► the chat's reply, what it recorded
GET  /api/clients, POST /api/reset, GET /    ──► app/web.py (the sample clients, the UI)

Every service and job of the product is declared here; operonx.toml only points at `APP`.
"""

from operonx.app import Application, Service, asgi, env, http

from app import web
from dashboard.graph import dashboard_api
from declare.graph import declare_api
from statements.graph import statement_api

PORT = env("PORT", 8030)

APP = Application(
    "mr-finance",
    description="Consolidate every asset a client holds, anywhere, into one picture — and say what is moving it.",
    services=[
        Service(
            "dashboard",
            http("POST", "/api/dashboard", port=PORT),
            graph=dashboard_api,
            description="POST {client_id, scope: personal|family, months}: the dashboard.",
        ),
        Service(
            "statement",
            http("POST", "/api/statement", port=PORT),
            graph=statement_api,
            description="POST {client_id, filename, content: base64}: a statement, read and kept.",
        ),
        Service(
            "declare",
            http("POST", "/api/declare", port=PORT),
            graph=declare_api,
            description="POST {client_id, message, session_id}: one chat turn of declarations.",
        ),
        # last: it is mounted at "/", and would answer every path the services above own
        Service("web", asgi("/", port=PORT), app=web.app, description="The UI and the sample clients."),
    ],
)

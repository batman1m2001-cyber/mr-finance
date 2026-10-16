"""The AI zone's own small door (app/zone.py): TCB's sync comes in at POST /api/zone/sync; GET /api/zone/status says
what the zone holds and sent (public news and its own records only)."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from control import config
from inbox import sign
from news import store as news_store
from zone import agent, mirror, sync


async def receive_sync(request: Request) -> JSONResponse:
    body = await request.body()
    if len(body) > 8 * 1024 * 1024:
        return JSONResponse({"error": "Gói quá lớn"}, status_code=413)
    code, reply = mirror.receive(body, request.headers.get(sign.HEADER))
    return JSONResponse(reply, status_code=code)


async def status(request: Request) -> JSONResponse:
    cats = {}
    for kind in sync.KINDS:
        a = config.active(kind)
        cats[kind] = {"id": a["id"], "from": a.get("mirrored_from")}
    return JSONResponse(
        {
            "zone": True,
            "news": len(news_store.inbox(status="all", limit=100000)),
            "last_ingest": news_store.last_run(),
            "catalogues": cats,
            "today": agent.made_today(),
            "cap": agent.cap(),
            "outbox": agent.recent(),
        }
    )


app = Starlette(
    routes=[Route("/api/zone/sync", receive_sync, methods=["POST"]), Route("/api/zone/status", status, methods=["GET"])]
)

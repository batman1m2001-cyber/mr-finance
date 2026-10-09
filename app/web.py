"""The web app beside the graphs: the UI (web/) and the plain reads it needs.

Listing the sample clients or resetting the demo is not a computation, so it is not a graph:
it is served here, by the asgi service app/main.py mounts last.
"""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from wealth import fixtures, store
from wealth.paths import DATA, ROOT


async def clients(request: Request) -> JSONResponse:
    out = []
    for cid in fixtures.client_ids():
        c = fixtures.client(cid)
        out.append(
            {
                **fixtures.summary(cid),
                "household": [{**m, "name": fixtures.client(m["id"])["name"]} for m in c.get("household", [])],
                "samples": c.get("samples", []),
            }
        )
    return JSONResponse({"clients": out, "as_of": fixtures.market()["as_of"]})


async def healthz(request: Request) -> JSONResponse:
    # operonx leaves /healthz to the asgi app when one is mounted at "/"
    return JSONResponse({"ok": True})


async def reset(request: Request) -> JSONResponse:
    store.reset()
    return JSONResponse({"reset": True})


app = Starlette(
    routes=[
        Route("/healthz", healthz),
        Route("/api/clients", clients),
        Route("/api/reset", reset, methods=["POST"]),
        # the sample statements a demo uploads
        Mount("/samples", app=StaticFiles(directory=DATA / "samples"), name="samples"),
        Mount("/", app=StaticFiles(directory=ROOT / "web", html=True), name="web"),
    ]
)

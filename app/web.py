"""The web app beside the graphs: the UI (web/) and the plain reads it needs.

Listing the sample clients or resetting the demo is not a computation, so it is not a graph:
it is served here, by the asgi service app/main.py mounts last.
"""

from __future__ import annotations

import json
from functools import lru_cache

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from apply import reads as apply_reads
from apply import run as apply_run
from apply import trace as apply_trace
from control import audit as control_audit
from control import db as control_db
from control import roles
from events import store as events_store
from news import ops as news_ops
from news import store as news_store
from scenarios._sim import SCENARIOS
from views import ops as view_ops
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


async def scenarios(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "scenarios": [
                {"id": k, "kind": v["kind"], "title": v["title"], "question": v["question"], "personas": v["personas"]}
                for k, v in SCENARIOS.items()
            ]
        }
    )


async def reviews(request: Request) -> JSONResponse:
    """The RM queue (newest first), for one client or all, by status."""
    q = request.query_params
    rows = store.reviews(client_id=q.get("client_id") or None, status=q.get("status") or None)
    names = {cid: fixtures.client(cid)["name"] for cid in fixtures.client_ids(members=True)}
    return JSONResponse({"items": [{**r, "client_name": names.get(r["client_id"], r["client_id"])} for r in rows]})


@lru_cache(maxsize=1)
def _advisory() -> dict:
    return json.loads((DATA / "advisory.json").read_text(encoding="utf-8"))


async def advisory(request: Request) -> JSONResponse:
    """A client's specialist team and advisory track record (data/advisory.json, mock), with the
    risk test they took in the demo, if any, as the last point of their risk-appetite history."""
    cid = request.query_params.get("client_id") or ""
    data = _advisory()
    if cid not in data["team"]:
        return JSONResponse({"error": f"no client {cid!r}"}, status_code=404)
    track = json.loads(json.dumps(data["tracking"][cid]))
    test = store.result(cid, "risk")
    if test:
        track["risk_tests"].append(
            {
                "date": test.get("taken"),
                "tolerance": round(test["tolerance"]),
                "capacity": round(test["capacity"]),
                "profile": (test.get("profile") or {}).get("name"),
                "live": True,
            }
        )
    return JSONResponse({"team": data["team"][cid], "tracking": track, "as_of": data["as_of"], "note": data["note"]})


async def advisory_all(request: Request) -> JSONResponse:
    """The advisory track record over every client (data/advisory.json, mock): the totals, each AI's
    average score and trend, one row per client, the latest advice and the news missed for anyone."""
    data = _advisory()
    tracks = data["tracking"]
    names = {cid: fixtures.client(cid)["name"] for cid in tracks}
    keys = next(iter(tracks.values()))["summary"].keys()
    summary = {k: sum(t["summary"][k] for t in tracks.values()) for k in keys}
    agents = []
    for i, a in enumerate(next(iter(tracks.values()))["agents"]):
        mine = [t["agents"][i] for t in tracks.values()]
        n = len(mine)
        agents.append(
            {
                "id": a["id"],
                "name": a["name"],
                "name_vi": a["name_vi"],
                "score": round(sum(x["score"] for x in mine) / n),
                "trend": [round(sum(x["trend"][j] for x in mine) / n, 3) for j in range(len(a["trend"]))],
                "by_client": [{"client": names[c], "score": t["agents"][i]["score"]} for c, t in tracks.items()],
            }
        )
    clients = [
        {
            "id": cid,
            "name": names[cid],
            **t["summary"],
            "scores": {a["id"]: a["score"] for a in t["agents"]},
            "alerts_opened": t["engagement"]["alerts_opened"],
        }
        for cid, t in tracks.items()
    ]
    advice = sorted(
        ({**x, "client": names[cid]} for cid, t in tracks.items() for x in t["advice"]),
        key=lambda x: x["date"],
        reverse=True,
    )
    missed: dict = {}
    for cid, t in tracks.items():
        for n in t["missed_news"]:
            m = missed.setdefault(n["title"], {**n, "impact": 0.0, "clients": []})
            m["impact"] += n["impact"]
            m["clients"].append(names[cid])
    months = next(iter(tracks.values()))["engagement"]["months"]
    engagement = {
        "months": months,
        **{
            k: [round(sum(t["engagement"][k][j] for t in tracks.values()) / len(tracks)) for j in range(len(months))]
            for k in ("minutes", "days")
        },
    }
    return JSONResponse(
        {
            "summary": summary,
            "agents": agents,
            "clients": clients,
            "advice": advice,
            "missed_news": sorted(missed.values(), key=lambda m: m["impact"]),
            "engagement": engagement,
            "as_of": data["as_of"],
            "note": data["note"],
        }
    )


@lru_cache(maxsize=1)
def _views() -> dict:
    return json.loads((DATA / "views.json").read_text(encoding="utf-8"))


async def views(request: Request) -> JSONResponse:
    """House views beside the headlines (data/views.json, mock): what research houses expect, and
    which holdings each is about — the page matches them to the client's own."""
    return JSONResponse(_views())


async def news_inbox(request: Request) -> JSONResponse:
    """The CIO's inbox (FR-103): newest first, by source, kind, status, relevance, time, words; and
    the feed-health strip: each source's last ingest and its items per hour over a day."""
    q = request.query_params
    try:
        since = float(q["since"]) if q.get("since") else None
        limit = min(int(q.get("limit") or 200), 1000)
    except ValueError:
        return JSONResponse({"error": "since and limit are numbers"}, status_code=400)
    if q.get("held"):
        items = [i for i in news_store.inbox(status="all", limit=5000) if i["held"]]
        cfg = news_ops.config()
        return JSONResponse({"items": items, "sources": [], "last_run": None, "config_version": cfg["version"]})
    items = news_store.inbox(
        source=q.get("source") or None,
        kind=q.get("kind") or None,
        status=q.get("status") or "new",
        relevance=q.get("relevance") or None,
        since=since,
        query=q.get("q") or None,
        limit=limit,
    )
    cfg = news_ops.config()
    last = news_store.last_run()
    hourly = news_store.counts_by_hour()
    sources = [
        {
            "id": s["id"],
            "outlet": s["outlet"],
            "section": s["section"],
            "kind": s["kind"],
            "last": (last or {}).get("sources", {}).get(s["id"]),
            "hourly": hourly.get(s["id"], [0] * 24),
        }
        for s in cfg["sources"]
    ]
    return JSONResponse({"items": items, "sources": sources, "last_run": last, "config_version": cfg["version"]})


async def events_list(request: Request) -> JSONResponse:
    """Every event, newest first, with its views (CIO workspace)."""
    out = []
    for ev in events_store.listing():
        out.append(
            {
                **{k: ev[k] for k in ("id", "title", "type", "created", "blocked", "held", "news_ids", "factors")},
                "views": view_ops.event_views(ev["id"]),
            }
        )
    return JSONResponse({"events": out})


async def event_one(request: Request) -> JSONResponse:
    try:
        ev = events_store.get(request.path_params["event_id"])
    except events_store.EventError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    return JSONResponse({"event": ev, "views": view_ops.event_views(ev["id"])})


async def view_one(request: Request) -> JSONResponse:
    """A view with its findings, decisions, agent runs (every node), approval checks and preview."""
    try:
        return JSONResponse(view_ops.public(request.path_params["view_id"]))
    except KeyError as exc:
        return JSONResponse({"error": str(exc.args[0])}, status_code=404)


async def agents_status(request: Request) -> JSONResponse:
    """Which mode an agent run would use now, the models, and the demo users (role switcher)."""
    return JSONResponse(
        {
            **view_ops.agent_status(),
            "users": [{"id": k, **v} for k, v in roles.USERS.items()],
            "note": "Bộ chuyển vai trò chỉ để demo, không phải cơ chế bảo mật.",
        }
    )


async def runs_list(request: Request) -> JSONResponse:
    """Application runs, newest first (CIO: all; ?role=rm: only those that passed post-check)."""
    q = request.query_params
    statuses = apply_run.RM_VISIBLE if q.get("role") == "rm" else None
    rows = apply_run.runs(view_id=q.get("view_id") or None, statuses=statuses)
    return JSONResponse({"runs": rows})


async def run_one(request: Request) -> JSONResponse:
    try:
        return JSONResponse({"run": apply_run.get(request.path_params["run_id"])})
    except KeyError as exc:
        return JSONResponse({"error": str(exc.args[0])}, status_code=404)


async def run_verify(request: Request) -> JSONResponse:
    """Recompute every family from the run's frozen snapshot and compare to the dong (NFR-04)."""
    try:
        return JSONResponse(apply_run.verify(request.path_params["run_id"]))
    except KeyError as exc:
        return JSONResponse({"error": str(exc.args[0])}, status_code=404)


async def family_impact(request: Request) -> JSONResponse:
    role = request.query_params.get("role") or "client"
    try:
        return JSONResponse(apply_reads.family_impact(request.path_params["family_id"], role))
    except roles.Forbidden as exc:
        return JSONResponse({"error": str(exc)}, status_code=403)


async def trace(request: Request) -> JSONResponse:
    """FR-406: a family's number back to the news (staff only: it names holdings)."""
    q = request.query_params
    try:
        return JSONResponse(
            apply_trace.trace(
                request.path_params["run_id"],
                request.path_params["family_id"],
                key=q.get("key") or None,
                horizon=q.get("horizon") or "3m",
            )
        )
    except KeyError as exc:
        return JSONResponse({"error": str(exc.args[0])}, status_code=404)


async def rm_today(request: Request) -> JSONResponse:
    return JSONResponse(apply_reads.rm_today())


async def audit_verify(request: Request) -> JSONResponse:
    with control_db.tx() as con:
        return JSONResponse(control_audit.verify(con))


async def audit_list(request: Request) -> JSONResponse:
    try:
        limit = min(int(request.query_params.get("limit") or 100), 1000)
    except ValueError:
        return JSONResponse({"error": "limit is a number"}, status_code=400)
    with control_db.tx() as con:
        rows = [dict(r) for r in con.execute("select * from audit_log order by seq desc limit ?", (limit,))]
    for r in rows:
        r["data"] = json.loads(r["data"])
    return JSONResponse({"rows": rows})


async def model(request: Request) -> JSONResponse:
    """The factor model the engine runs on: factors, sizes, realisation, volatilities, the stressed
    repair — every assumed parameter flagged (B1)."""
    from engine import ENGINE_VERSION, default_model

    m = default_model()
    vol_s = m.vol("stressed")
    return JSONResponse({
        "version": m.version, "hash": m.hash, "status": m.status, "note": m.note, "engine_version": ENGINE_VERSION,
        "horizons": m.horizons, "priced_in": m.priced_in, "core_uncertainty": m.core_uncertainty,
        "stressed_repair": m.stressed_repair, "loadings": m.loadings,
        "factors": [{"id": f.id, "name": f.name, "group": f.group, "unit": f.unit, "sizes": f.sizes,
                     "realisation": f.realisation, "vol_month": f.vol_month, "vol_month_stressed": round(vs, 4),
                     "brd_parameter": f.brd_parameter, "assumed": f.assumed} for f, vs in zip(m.factors, vol_s)],
        "correlations": {"ids": m.ids, "normal": [[round(x, 3) for x in r] for r in m.corr["normal"]],
                         "stressed": [[round(x, 3) for x in r] for r in m.corr["stressed"]]},
    })


async def news_config(request: Request) -> JSONResponse:
    """The white list and the (mock) restricted list Compliance owns."""
    cfg = news_ops.config()
    return JSONResponse({k: cfg[k] for k in ("version", "note", "gates", "sources", "restricted", "event_types")})


async def reset(request: Request) -> JSONResponse:
    store.reset()
    news_store.reset()
    control_db.reset()
    return JSONResponse({"reset": True})


app = Starlette(
    routes=[
        Route("/healthz", healthz),
        Route("/api/clients", clients),
        Route("/api/scenarios", scenarios),
        Route("/api/review", reviews),
        Route("/api/advisory", advisory),
        Route("/api/advisory/all", advisory_all),
        Route("/api/views", views),
        Route("/api/news/inbox", news_inbox),
        Route("/api/news/config", news_config),
        Route("/api/model", model),
        Route("/api/events", events_list),
        Route("/api/events/{event_id}", event_one),
        Route("/api/views/{view_id}", view_one),
        Route("/api/agents", agents_status),
        Route("/api/runs", runs_list),
        Route("/api/runs/{run_id}", run_one),
        Route("/api/runs/{run_id}/verify", run_verify),
        Route("/api/families/{family_id}/impact", family_impact),
        Route("/api/trace/{run_id}/{family_id}", trace),
        Route("/api/rm/today", rm_today),
        Route("/api/audit", audit_list),
        Route("/api/audit/verify", audit_verify),
        Route("/api/reset", reset, methods=["POST"]),
        # the sample statements a demo uploads
        Mount("/samples", app=StaticFiles(directory=DATA / "samples"), name="samples"),
        Mount("/", app=StaticFiles(directory=ROOT / "web", html=True), name="web"),
    ]
)

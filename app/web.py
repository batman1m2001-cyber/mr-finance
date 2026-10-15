"""The web app beside the graphs: the UI (web/) and the plain reads it needs.

Listing the sample clients or resetting the demo is not a computation, so it is not a graph:
it is served here, by the asgi service app/main.py mounts last.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache

from starlette.applications import Starlette
from starlette.datastructures import Headers, QueryParams
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from apply import impact_graph
from apply import reads as apply_reads
from apply import run as apply_run
from apply import trace as apply_trace
from control import audit as control_audit
from control import db as control_db
from control import roles
from events import store as events_store
from market import factors as market_factors
from market import fetch as market_fetch
from market import store as market_store
from news import ops as news_ops
from news import store as news_store
from people import auth as people_auth
from people import store as people_store
from research import ops as research_ops
from research import store as research_store
from scenarios._sim import SCENARIOS
from views import ops as view_ops
from wealth import fixtures, store
from wealth.paths import DATA, ROOT


class Revalidated(StaticFiles):
    """The UI's files, which a browser checks again on every load (a 304 when unchanged): the pages are ES modules
    that import each other, and a module kept from before a deploy beside one from after it breaks the page."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


def viewer(request: Request):
    """The person signed in (SignInGate), or None when sign-in is off."""
    return request.scope.get("mf_viewer")


def _visible_clients(v) -> list:
    if v is None or v["role"] in ("cio", "compliance", "admin"):
        return fixtures.client_ids()
    if v["role"] == "rm":
        return [c for c in fixtures.client_ids() if c in v.get("families", [])]
    return [v["family"]]


async def clients(request: Request) -> JSONResponse:
    """The families the person signed in may see: a client their own, an RM the families assigned to them."""
    out = []
    for cid in _visible_clients(viewer(request)):
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
    """Liveness, and which protections are on or off right now (BRD §13, RULE-SEC-10)."""
    # operonx leaves /healthz to the asgi app when one is mounted at "/"
    from copilot import router as copilot_router
    from wealth import ai

    agents = view_ops.agent_status()
    hmac_on = bool((os.environ.get("AUDIT_HMAC_KEY") or "").strip())
    router_by = "mô hình " + copilot_router.model() if copilot_router.live() else "từ khóa"
    protections = [
        {
            "id": "audit_hmac",
            "on": hmac_on,
            "note": "Chuỗi nhật ký ký HMAC"
            if hmac_on
            else "Chuỗi nhật ký chỉ SHA-256: ai ghi được cơ sở dữ liệu có thể tính lại cả chuỗi",
        },
        {
            "id": "two_models",
            "on": agents["mode"] == "live",
            "note": "Agent CIO và phản biện dùng hai mô hình khác nhau"
            if agents["mode"] == "live"
            else "Agent chạy mô phỏng (chưa cấu hình hai mô hình)",
        },
        {
            "id": "client_text_off_ai",
            "on": not ai.enabled(),
            "note": "Bước đọc sao kê và chat khai báo không gửi dữ liệu khách cho AI"
            if not ai.enabled()
            else "AI đang bật: bước đọc sao kê và chat khai báo gửi nội dung của khách cho mô hình "
            "(docs/TO_DISCUSS.md D-03)",
        },
        {
            "id": "copilot_router",
            "on": True,
            "note": f"Copilot định tuyến bằng {router_by}; mô hình không đọc dữ liệu khách",
        },
        {
            "id": "sign_in",
            "on": people_auth.enabled(),
            "note": (
                "Đăng nhập bắt buộc; phiên ký HMAC" if people_auth.enabled() else "Đăng nhập đang tắt (MF_AUTH=off)"
            )
            + ("; danh sách tài khoản demo đang mở (MF_DEMO_ACCOUNTS)" if people_auth.demo_accounts_on() else ""),
        },
    ]
    return JSONResponse({"ok": True, "protections": protections, "off": [p["id"] for p in protections if not p["on"]]})


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
    mine = set(_visible_clients(viewer(request)))
    heads = {cid: fixtures.client(cid).get("member_of") or cid for cid in fixtures.client_ids(members=True)}
    rows = [r for r in rows if heads.get(r["client_id"], r["client_id"]) in mine]
    names = {cid: fixtures.client(cid)["name"] for cid in heads}
    return JSONResponse({"items": [{**r, "client_name": names.get(r["client_id"], r["client_id"])} for r in rows]})


@lru_cache(maxsize=1)
def _advisory() -> dict:
    return json.loads((DATA / "advisory.json").read_text(encoding="utf-8"))


async def advisory(request: Request) -> JSONResponse:
    """A client's team (the people table) and advisory track record (data/advisory.json, mock), with the
    risk test they took in the demo, if any, as the last point of their risk-appetite history."""
    cid = request.query_params.get("client_id") or ""
    data = _advisory()
    team = people_store.team(cid)
    if team is None or cid not in data["tracking"]:
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
    return JSONResponse({"team": team, "tracking": track, "as_of": data["as_of"], "note": data["note"]})


async def advisory_all(request: Request) -> JSONResponse:
    """The advisory track record over every client (data/advisory.json, mock): the totals, each AI's
    average score and trend, one row per client, the latest advice and the news missed for anyone."""
    data = _advisory()
    mine = set(_visible_clients(viewer(request)))
    tracks = {cid: t for cid, t in data["tracking"].items() if cid in mine}
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
            "users": [{"id": k, **v} for k, v in roles.users().items()],
            "note": "Bộ chuyển vai trò chỉ để demo, không phải cơ chế bảo mật.",
        }
    )


async def config_list(request: Request) -> JSONResponse:
    """FR-701: every kind of configuration, its version in force, a pending proposal, the history."""
    from control import config

    return JSONResponse({"kinds": config.overview(), "users": [{"id": k, **v} for k, v in roles.users().items()]})


async def config_version(request: Request) -> JSONResponse:
    from control import config

    vid = request.path_params["version_id"]
    kind = vid[3:].rsplit("-v", 1)[0]
    try:
        return JSONResponse(next(v for v in config.versions(kind) if v["id"] == vid))
    except (StopIteration, ValueError):
        return JSONResponse({"error": f"không có phiên bản {vid}"}, status_code=404)


async def agent_catalogue(request: Request) -> JSONResponse:
    """FR-703 agent catalogue and RULE-MEAS-04 AI quality (?days=7)."""
    from views import catalogue

    try:
        days = max(1, min(int(request.query_params.get("days") or 7), 365))
    except ValueError:
        return JSONResponse({"error": "days is a number"}, status_code=400)
    return JSONResponse({**catalogue.catalogue(), "quality": catalogue.quality(days)})


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


async def run_graph(request: Request) -> JSONResponse:
    """UI redesign R4: the CIO's whole run as a graph (every family it computed)."""
    try:
        return JSONResponse(impact_graph.run_graph(request.path_params["run_id"]))
    except KeyError as exc:
        return JSONResponse({"error": str(exc.args[0])}, status_code=404)


async def run_verify(request: Request) -> JSONResponse:
    """Recompute every family from the run's frozen snapshot and compare to the dong (NFR-04)."""
    try:
        return JSONResponse(apply_run.verify(request.path_params["run_id"]))
    except KeyError as exc:
        return JSONResponse({"error": str(exc.args[0])}, status_code=404)


async def family_impact(request: Request) -> JSONResponse:
    role = _role_view(request)
    try:
        return JSONResponse(apply_reads.family_impact(request.path_params["family_id"], role))
    except roles.Forbidden as exc:
        return JSONResponse({"error": str(exc)}, status_code=403)


async def family_graph(request: Request) -> JSONResponse:
    """Kit K3: news → event → scenario → factor → asset → family → goal, every edge with its records."""
    q = request.query_params
    try:
        return JSONResponse(
            impact_graph.family_graph(request.path_params["family_id"], _role_view(request), q.get("run_id") or None)
        )
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
    v = viewer(request)
    return JSONResponse(apply_reads.rm_today(v.get("families") if v else None))


async def audit_verify(request: Request) -> JSONResponse:
    with control_db.tx() as con:
        return JSONResponse(control_audit.verify(con))


async def audit_export(request: Request):
    """FR-702 export: ?format=json (default, with the chain check) or csv (one row per entry)."""
    import csv
    import io
    from datetime import datetime, timezone

    from starlette.responses import Response

    with control_db.tx() as con:
        out = control_audit.export(con)
    stamp = datetime.fromtimestamp(out["exported"], timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if request.query_params.get("format") == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["seq", "ts_utc", "actor", "action", "object", "alg", "prev_hash", "hash", "data"])
        for r in out["rows"]:
            ts = datetime.fromtimestamp(r["ts"], timezone.utc).isoformat()
            w.writerow(
                [
                    r["seq"],
                    ts,
                    r["actor"],
                    r["action"],
                    r["object"],
                    r["alg"],
                    r["prev_hash"],
                    r["hash"],
                    json.dumps(r["data"], ensure_ascii=False, sort_keys=True),
                ]
            )
        return Response(
            buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={"content-disposition": f'attachment; filename="audit-{stamp}.csv"'},
        )
    return JSONResponse(out, headers={"content-disposition": f'attachment; filename="audit-{stamp}.json"'})


async def market(request: Request) -> JSONResponse:
    """The source registry and the stored market data (F1): each job's cadence, last run, last success and last
    error; each series' coverage, last value and source; each factor's provenance (from SQLite only)."""
    from datetime import date, timedelta

    cat = market_fetch.catalogue()
    health = market_store.job_health()
    since = (date.today() - timedelta(days=120)).isoformat()
    cov = market_store.coverage()
    jobs = [{"id": j, **meta, **health.get(j, {})} for j, meta in cat["jobs"].items()]
    series = [
        {
            "id": s["id"],
            "name": s["name"],
            "unit": s["unit"],
            "job": s["job"],
            "sources": [x["source"] for x in s["sources"]],
            "factor": s.get("factor"),
            "note": s.get("note"),
            **{k: v for k, v in (cov.get(s["id"]) or {}).items() if k != "series"},
            "tail": [v for _, v in market_store.points(s["id"], start=since)],
        }
        for s in cat["series"]
    ]
    return JSONResponse(
        {"jobs": jobs, "series": series, "factors": market_factors.factor_series(), "note": cat.get("note")}
    )


async def market_series(request: Request) -> JSONResponse:
    """One series' points (stored or computed), from ``from`` (ISO date) on."""
    sid = request.query_params.get("id") or ""
    known = {s["id"] for s in market_fetch.catalogue()["series"]} | set(market_factors.COMPUTED)
    if sid not in known:
        return JSONResponse({"error": f"không có chuỗi {sid!r}"}, status_code=404)
    since = request.query_params.get("from") or ""
    pts = [p for p in market_factors.values(sid) if p[0] >= since]
    return JSONResponse({"id": sid, "points": pts})


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
    from control import config as control_config
    from engine import ENGINE_VERSION, default_model

    m = default_model()
    vol_s = m.vol("stressed")
    raw = {f["id"]: f for f in control_config.data("factor_model")["factors"]}
    return JSONResponse(
        {
            "version": m.version,
            "hash": m.hash,
            "status": m.status,
            "note": m.note,
            "engine_version": ENGINE_VERSION,
            "horizons": m.horizons,
            "priced_in": m.priced_in,
            "core_uncertainty": m.core_uncertainty,
            "stressed_repair": m.stressed_repair,
            "loadings": m.loadings,
            "factors": [
                {
                    "id": f.id,
                    "name": f.name,
                    "group": f.group,
                    "unit": f.unit,
                    "sizes": f.sizes,
                    "realisation": f.realisation,
                    "vol_month": f.vol_month,
                    "vol_month_stressed": round(vs, 4),
                    "brd_parameter": f.brd_parameter,
                    "assumed": f.assumed,
                    "estimated": raw.get(f.id, {}).get("estimated"),
                }
                for f, vs in zip(m.factors, vol_s)
            ],
            "correlations": {
                "ids": m.ids,
                "normal": [[round(x, 3) for x in r] for r in m.corr["normal"]],
                "stressed": [[round(x, 3) for x in r] for r in m.corr["stressed"]],
            },
        }
    )


async def model_estimate_preview(request: Request) -> JSONResponse:
    """What estimating now would give (F2), against the model in force, and the out-of-sample check (MEAS-08):
    computed from the stored history, nothing proposed."""
    from control import config as control_config
    from market import estimate

    base = control_config.data("factor_model")
    q = request.query_params
    hist = estimate.history()
    est = estimate.estimate(base, end=q.get("end") or None, hist=hist)
    val = estimate.validate(base, split=q.get("split") or "2024-01", hist=hist)
    return JSONResponse({"report": est["report"], "validation": val, "in_force": base["version"]})


async def accuracy(request: Request) -> JSONResponse:
    """FEAT-18: the model walked forward over history, and every approved view's forecasts scored as their horizons
    pass (BR-15, KPI-03/04, MEAS-01/02)."""
    from measure import backtest, forecasts

    rows = forecasts.all_rows()
    views = {}
    for r in rows:
        v = views.setdefault(r["view_id"], {"view_id": r["view_id"], "event_id": r.get("event_id"),
                                            "origin": r["origin"], "late": r.get("late"), "model": r.get("model"),
                                            "forecasts": []})
        v["forecasts"].append({k: r.get(k) for k in ("factor", "horizon", "due", "expected", "p10", "p50", "p90",
                                                      "unit", "result", "realised", "inside", "direction_hit")})
    return JSONResponse({
        "history": backtest.cached(),
        "views": forecasts.summary(rows),
        "recorded": sorted(views.values(), key=lambda v: v["origin"], reverse=True),
        "min_obs": backtest.MIN_OBS,
        "accept": list(backtest.ACCEPT),
        "direction_target": backtest.DIRECTION_TARGET,
    })


async def measure_reports(request: Request) -> JSONResponse:
    """The monthly measurement reports: misses (MEAS-03), rubber-stamping (MEAS-05), news to RM (KPI-01, WF-09),
    inbox and agent timing (NFR-02)."""
    from measure import reports

    return JSONResponse(reports.all_reports())


async def news_config(request: Request) -> JSONResponse:
    """The white list and the (mock) restricted list Compliance owns."""
    cfg = news_ops.config()
    return JSONResponse({k: cfg[k] for k in ("version", "note", "gates", "sources", "restricted", "event_types")})


async def research_list(request: Request) -> JSONResponse:
    """Uploaded research and regulation notes with their status (CIO, Compliance)."""
    return JSONResponse(
        {"items": research_store.listing(request.query_params.get("status") or None), "kinds": research_store.KINDS}
    )


async def goal_regulation(request: Request) -> JSONResponse:
    """The goal branch (FR-602/603): released regulation notes matched to goals. ?role=client keeps
    only declared goals with a client message; staff see every match, RM tasks included."""
    from datetime import date

    from procedural.goals import PURPOSES, goals_of

    q = request.query_params
    fid = q.get("family_id") or None
    rows = research_ops.matches(fid)
    if q.get("role") == "client":
        rows = [
            {
                k: r[k]
                for k in (
                    "goal",
                    "need_date",
                    "purpose_label",
                    "country",
                    "milestone",
                    "level",
                    "level_label",
                    "documents",
                    "client_message",
                )
            }
            for r in rows
            if r["client_message"]
        ]
    out = {"matches": rows, "purposes": PURPOSES}
    if fid and q.get("role") != "client":
        decl = research_store.declared()
        out["goals"] = [{**g, "declared": decl.get(g["goal_id"])} for g in goals_of(fixtures.client(fid), date.today())]
    return JSONResponse(out)


async def reset(request: Request) -> JSONResponse:
    store.reset()
    news_store.reset()
    control_db.reset()
    people_store.reset()
    people_auth.reset()
    return JSONResponse({"reset": True})


def _role_view(request: Request) -> str:
    """Which view of a family's impact: ``?role=`` for staff; a client always gets the client view (ADR-0008)."""
    v = viewer(request)
    if v is not None and v["role"] == "client":
        return "client"
    return request.query_params.get("role") or "client"


# -- sign-in (BRD-RULE-SEC-01; src/people/auth.py) --------------------------------------------------


def _cookie(request: Request, response: JSONResponse, token: str) -> JSONResponse:
    https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(
        people_auth.COOKIE, token, max_age=people_auth.TTL, httponly=True, samesite="lax", secure=https, path="/"
    )
    return response


def _audit_sign_in(person_id: str, how: str) -> None:
    with control_db.tx() as con:
        control_audit.append(con, person_id, "auth.sign_in", person_id, {"how": how})


async def auth_me(request: Request) -> JSONResponse:
    """Who is signed in (``user`` null when nobody), and whether the sign-in page may list demo accounts."""
    on = people_auth.enabled()
    v = people_auth.from_cookie_header(request.headers.get("cookie")) if on else None
    return JSONResponse({"user": v, "auth": on, "demo_accounts": on and people_auth.demo_accounts_on()})


async def auth_accounts(request: Request) -> JSONResponse:
    """The demo accounts the sign-in page lists, only while MF_DEMO_ACCOUNTS is on."""
    if not people_auth.demo_accounts_on():
        return JSONResponse({"accounts": []})
    rows = [a for a in people_auth.accounts()]
    return JSONResponse(
        {"accounts": [{k: a[k] for k in ("id", "name", "role", "title", "member_of", "login")} for a in rows]}
    )


async def _json(request: Request) -> dict:
    try:
        body = await request.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


async def auth_login(request: Request) -> JSONResponse:
    import asyncio

    body = await _json(request)
    token = people_auth.login(str(body.get("login") or ""), str(body.get("password") or ""))
    if token is None:
        await asyncio.sleep(0.4)  # slows guessing; the answer is the same for an unknown login
        return JSONResponse({"error": "Sai tên đăng nhập hoặc mật khẩu"}, status_code=401)
    v = people_auth.verify(token)
    _audit_sign_in(v["id"], "password")
    return _cookie(request, JSONResponse({"user": v}), token)


async def auth_demo(request: Request) -> JSONResponse:
    body = await _json(request)
    token = people_auth.demo_login(str(body.get("id") or ""))
    if token is None:
        return JSONResponse({"error": "Tài khoản demo không mở"}, status_code=403)
    v = people_auth.verify(token)
    _audit_sign_in(v["id"], "demo")
    return _cookie(request, JSONResponse({"user": v}), token)


async def auth_logout(request: Request) -> JSONResponse:
    response = JSONResponse({"signed_out": True})
    response.delete_cookie(people_auth.COOKIE, path="/")
    return response


# what a customer may not open, and what only an RM opens
STAFF_ONLY = (
    "/api/advisory/all",
    "/api/news",
    "/api/model",
    "/api/events",
    "/api/agents",
    "/api/config",
    "/api/runs",
    "/api/audit",
    "/api/market",
    "/api/accuracy",
    "/api/measure",
    "/api/research",
    "/api/rm/",
    "/api/trace/",
)
OPEN = ("/healthz", "/api/auth/")


def _deny(status: int, message: str) -> JSONResponse:
    return JSONResponse({"error": message, "sign_in": status == 401}, status_code=status)


def _family_of(path: str, query: QueryParams):
    parts = path.split("/")
    if path.startswith("/api/families/") and len(parts) > 3:
        return parts[3]
    if path.startswith("/api/trace/") and len(parts) > 4:
        return parts[4]
    return query.get("client_id") or query.get("family_id") or None


class SignInGate:
    """Every /api/ read needs a session (sign-in on): a customer never opens a staff read, only an RM opens the RM
    reads, and a family's data opens only for whoever may see it (people.auth.may_see)."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        if (
            scope["type"] != "http"
            or not path.startswith("/api/")
            or path.startswith(OPEN)
            or not people_auth.enabled()
        ):
            return await self.app(scope, receive, send)
        v = people_auth.from_cookie_header(Headers(scope=scope).get("cookie"))
        if v is None:
            return await _deny(401, "Cần đăng nhập")(scope, receive, send)
        if v["role"] == "client" and path.startswith(STAFF_ONLY):
            return await _deny(403, "Trang này dành cho nhân viên")(scope, receive, send)
        if path.startswith("/api/rm/") and v["role"] != "rm":
            return await _deny(403, "Trang này dành cho RM")(scope, receive, send)
        fam = _family_of(path, QueryParams(scope.get("query_string", b"")))
        if fam and not people_auth.may_see(v, fam):
            return await _deny(403, f"{v['name']} không được xem dữ liệu của khách hàng này")(scope, receive, send)
        scope["mf_viewer"] = v
        return await self.app(scope, receive, send)


app = Starlette(
    routes=[
        Route("/api/auth/me", auth_me),
        Route("/api/auth/accounts", auth_accounts),
        Route("/api/auth/login", auth_login, methods=["POST"]),
        Route("/api/auth/demo", auth_demo, methods=["POST"]),
        Route("/api/auth/logout", auth_logout, methods=["POST"]),
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
        Route("/api/model/estimate", model_estimate_preview),
        Route("/api/events", events_list),
        Route("/api/events/{event_id}", event_one),
        Route("/api/views/{view_id}", view_one),
        Route("/api/agents", agents_status),
        Route("/api/agents/catalogue", agent_catalogue),
        Route("/api/config", config_list),
        Route("/api/config/{version_id}", config_version),
        Route("/api/runs", runs_list),
        Route("/api/runs/{run_id}", run_one),
        Route("/api/runs/{run_id}/verify", run_verify),
        Route("/api/runs/{run_id}/graph", run_graph),
        Route("/api/families/{family_id}/impact", family_impact),
        Route("/api/families/{family_id}/graph", family_graph),
        Route("/api/trace/{run_id}/{family_id}", trace),
        Route("/api/rm/today", rm_today),
        Route("/api/audit", audit_list),
        Route("/api/market", market),
        Route("/api/accuracy", accuracy),
        Route("/api/measure", measure_reports),
        Route("/api/market/series", market_series),
        Route("/api/research", research_list),
        Route("/api/goals/regulation", goal_regulation),
        Route("/api/audit/verify", audit_verify),
        Route("/api/audit/export", audit_export),
        Route("/api/reset", reset, methods=["POST"]),
        # the sample statements a demo uploads
        Mount("/samples", app=StaticFiles(directory=DATA / "samples"), name="samples"),
        Mount("/", app=Revalidated(directory=ROOT / "web", html=True), name="web"),
    ]
)
app = SignInGate(app)

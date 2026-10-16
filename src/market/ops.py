"""The market jobs' steps: one op per kind of data, each fetching its job's series into SQLite (F1, F-D2).

``since`` (an ISO date) makes a run a backfill from that day; ``only`` limits it to some series. ``tick`` and
``at`` are what a schedule sends and are not used. Each returns the run's summary: per series, the source used,
the points kept and the error, if any (also in ``source_runs``)."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Optional

from operonx import op

from market import estimate, fetch, store


async def _run(job: str, since: Optional[str], only: Optional[list]) -> dict:
    start = date.fromisoformat(since) if since else None
    return await asyncio.to_thread(fetch.run_job, job, None, None, start, only)


@op
async def equity_bars(since: str = None, only: list = None) -> dict:
    """VN-Index and the demo's stocks: daily closes (VNDirect, then Vietcap)."""
    return {"run": await _run("market_equity", since, only)}


@op
async def foreign_flow(since: str = None, only: list = None) -> dict:
    """Foreign investors' net buying on HOSE (cafef)."""
    return {"run": await _run("market_flows", since, only)}


@op
async def gov_yields(since: str = None, only: list = None) -> dict:
    """Vietnam government bond yields by tenor (HNX curve, then worldgovernmentbonds for 10 years)."""
    return {"run": await _run("market_yields", since, only)}


@op
async def fx_rates(since: str = None, only: list = None) -> dict:
    """USD/VND (Vietcombank, then MSN)."""
    return {"run": await _run("market_fx", since, only)}


@op
async def world_series(since: str = None, only: list = None) -> dict:
    """Gold, Brent, world equities, the S&P 500, the US 10-year and the DXY's six currencies (MSN, one request)."""
    return {"run": await _run("market_world", since, only)}


@op
async def crypto_bars(since: str = None, only: list = None) -> dict:
    """Bitcoin and Ether in USD (Binance)."""
    return {"run": await _run("market_crypto", since, only)}


@op
async def sjc_gold(since: str = None, only: list = None) -> dict:
    """SJC gold bars' selling price in Ho Chi Minh City (PNJ's history)."""
    return {"run": await _run("market_gold", since, only)}


@op
async def backfill(since: str = "2020-01-01", only: list = None) -> dict:
    """Every job's series from ``since`` (default 2020-01): on demand, `operonx run market_backfill`."""
    out = []
    for job in fetch.jobs():
        out.append(await _run(job, since or "2020-01-01", only))
    return {"run": {"job": "market_backfill", "jobs": out, "points": sum(r["points"] for r in out)}}


@op
def ask_load(by: str, since: str = "2020-01-01") -> dict:
    """An Admin asks for the market history to be loaded again from ``since`` (Hệ thống). Queued: the
    ``market_load`` job runs it within a minute; one load at a time."""
    from control import audit, db, roles
    from control.errors import BadRequest

    roles.require(by, "admin")
    since = str(since or "2020-01-01")
    try:
        start = date.fromisoformat(since)
    except ValueError:
        raise BadRequest(f"since {since!r}: một ngày dạng YYYY-MM-DD") from None
    if not date(2015, 1, 1) <= start <= date.today():
        raise BadRequest("since: từ 2015-01-01 đến hôm nay")
    req = store.request_load(by, since)
    if req["queued"]:
        with db.tx() as con:
            audit.append(con, by, "market.load_asked", f"LOAD-{req['id']}", {"since": since})
    return {"load": req}


@op
async def run_loads(tick: int = None, at: str = None) -> dict:
    """The ``market_load`` job: the load an Admin asked for, if any (every series from its ``since``)."""
    return {"load": await load_pending()}


async def load_pending() -> Optional[dict]:
    """The oldest load waiting, run; None when none waits."""
    req = store.next_load()
    if req is None:
        return None
    try:
        out = []
        for job in fetch.jobs():
            out.append(await _run(job, req["since"], None))
        points = sum(r["points"] for r in out)
        errors = sum(r["errors"] for r in out)
        note = f"{errors} chuỗi không lấy được (xem Dữ liệu thị trường)" if errors else None
        store.finish_load(req["id"], points, note, failed=points == 0 and errors > 0)
    except Exception as exc:  # noqa: BLE001 — a crash is a failed load the Admin must see, not a stuck one
        store.finish_load(req["id"], 0, f"{type(exc).__name__}: {exc}"[:500], failed=True)
    return store.loads(1)[0]


@op
def propose_estimate(by: str, end: str = None, note: str = "") -> dict:
    """A CIO proposes the model estimated from the stored history as the next ``factor_model`` version (F2); a
    second CIO approves it in Cấu hình (ADR-0016). Nothing changes until then."""
    from control import config, roles

    roles.user(by)
    roles.require(by, "cio")
    est = estimate.estimate(config.data("factor_model"), end=end or None)
    if not est["report"]["estimated"]:
        raise ValueError("chưa đủ dữ liệu: chưa yếu tố nào có từ 24 tháng (chạy market_backfill)")
    why = note or (
        f"Ước lượng {est['report']['estimated']}/15 yếu tố từ {est['report']['start']} đến {est['report']['end']}, "
        f"co tương quan {round(est['report']['shrinkage'] * 100)} %"
    )
    version = config.propose("factor_model", est["model"], by, why)
    return {"version": version, "report": est["report"]}

"""The AI zone's agent (ZONE-02, AI-13 inbox mode): every tick, the packages not yet delivered are sent again; then,
under the day's cap (``MF_ZONE_DAILY``, default 6 events), the most-covered event type among the zone's own fresh
news becomes an event, the CIO agent runs on it (the same ``cio_agent_flow`` as at TCB, with TCB's approved prompts
and models), and the result goes to TCB's inbox as a signed package (``MF_INBOX_KEY``). The zone reads nothing back:
TCB answers an id. A package TCB does not take is tried again for a day (``zone_outbox``)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from control import db
from control.roles import ZONE_ACTOR
from events import store as events
from inbox import importer, sign
from news import store as news_store
from views import agents
from views import store as vstore
from wealth.paths import in_zone
from zone import sync

FRESH_S = 48 * 3600
GIVE_UP_S = 24 * 3600
MAX_NEWS = 8


def cap() -> int:
    try:
        return max(0, int(os.environ.get("MF_ZONE_DAILY") or 6))
    except ValueError:
        return 6


def tcb_inbox() -> str:
    return (os.environ.get("MF_TCB_INBOX") or "").strip()


def candidates(now: Optional[float] = None) -> List[Dict[str, Any]]:
    """The news of the event type most covered in the last two days (not held, at least medium relevance), newest
    first, at most eight."""
    now = now or time.time()
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for it in news_store.inbox(status="new", limit=1000):
        fresh = (it.get("published") or it["ingested"]) >= now - FRESH_S
        if fresh and not it["held"] and it.get("event_type") and it.get("relevance") in ("high", "medium"):
            groups[it["event_type"]].append(it)
    if not groups:
        return []
    best = max(groups.values(), key=lambda g: (len(g), max(i.get("published") or i["ingested"] for i in g)))
    return best[:MAX_NEWS]


def made_today(now: Optional[float] = None) -> int:
    lt = time.localtime(now or time.time())
    midnight = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1))
    with db.tx() as con:
        return con.execute("select count(*) from zone_outbox where created >= ?", (midnight,)).fetchone()[0]


def package(view_id: str) -> Dict[str, Any]:
    """The view as TCB's import reads it (inbox.importer): the event's news by reference and address, the view with
    those references, the challenger's findings, and the run's trace."""
    v = vstore.get(view_id)
    ev = events.get(v["event_id"])
    refs = {n["id"]: f"Z{k + 1}" for k, n in enumerate(ev["news"])}
    runs = vstore.runs(view_id)
    cio = next(r for r in runs if r["agent"] == "cio")
    ch = vstore.latest_challenge(view_id) or {"findings": []}
    return {
        "version": importer.VERSION,
        "zone_run": cio["id"],
        "created": time.time(),
        "event": {"title": ev["title"], "type": ev.get("type")},
        "news": [
            {"ref": refs[n["id"]], "url": n["url"], "title": n["title"], "source": n["source"]} for n in ev["news"]
        ],
        "view": importer._remap(v["current"], refs),
        "challenge": {"findings": ch["findings"]},
        "run": {
            "mode": v["mode"],
            "models": v["models"],
            "prompt_version": agents.prompt_version(),
            "nodes": [{k: x for k, x in n.items() if k != "seq"} for n in cio["nodes"]],
        },
    }


def _body(pkg: Dict[str, Any]) -> bytes:
    from inbox import store as inbox_store

    body = json.dumps(pkg, ensure_ascii=False).encode("utf-8")
    if len(body) > inbox_store.MAX_BYTES * 0.9:  # the trace without the prompts and inputs, to fit TCB's door
        pkg["run"]["nodes"] = [
            {k: x for k, x in n.items() if k not in ("prompt", "input")} for n in pkg["run"]["nodes"]
        ]
        body = json.dumps(pkg, ensure_ascii=False).encode("utf-8")
    return body


def _add(event_id: str, data: Dict[str, Any], status: str) -> str:
    with db.tx() as con:
        oid = f"OB-{db.next_seq(con, 'zone_outbox'):06d}"
        con.execute(
            "insert into zone_outbox values (?, ?, ?, ?, ?)", (oid, event_id, status, time.time(), db.dumps(data))
        )
    return oid


def _set(oid: str, status: str, **changes: Any) -> Dict[str, Any]:
    with db.tx() as con:
        row = db.load(con.execute("select * from zone_outbox where id = ?", (oid,)).fetchone())
        data = {k: v for k, v in row.items() if k not in ("id", "event_id", "status", "created")}
        data.update(changes)
        con.execute("update zone_outbox set status = ?, data = ? where id = ?", (status, db.dumps(data), oid))
    return {**row, **changes, "status": status}


def deliver(oid: str, send: Optional[sync.Send] = None) -> Dict[str, Any]:
    """One package to TCB's inbox: ``sent`` with TCB's id on 202; otherwise ``waiting`` (tried again next tick) until
    a day has passed, then ``failed``."""
    with db.tx() as con:
        row = db.load(con.execute("select * from zone_outbox where id = ?", (oid,)).fetchone())
    body = row["package"].encode("utf-8")
    url = tcb_inbox()
    attempts = row.get("attempts", 0) + 1
    if not url:
        code, reply = 0, {"error": "Chưa đặt MF_TCB_INBOX"}
    else:
        key = sign.key()
        headers = {sign.HEADER: sign.sign(body, key)} if key else {}
        try:
            code, reply = (send or sync.post)(url, body, headers)
        except Exception as exc:  # noqa: BLE001 — TCB not answering: tried again next tick
            code, reply = 0, {"error": f"{type(exc).__name__}: {exc}"[:300]}
    if code == 202:
        return _set(oid, "sent", attempts=attempts, tcb_id=reply.get("id"), sent_at=time.time(), last_error=None)
    why = str(reply.get("error") or f"HTTP {code}")[:300]
    status = "failed" if time.time() - row["created"] > GIVE_UP_S else "waiting"
    return _set(oid, status, attempts=attempts, last_error=why)


def waiting() -> List[str]:
    with db.tx() as con:
        return [r[0] for r in con.execute("select id from zone_outbox where status = 'waiting' order by created")]


def recent(limit: int = 20) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = [db.load(r) for r in con.execute("select * from zone_outbox order by created desc limit ?", (limit,))]
    return [{k: v for k, v in r.items() if k != "package"} for r in rows]


async def run_agent(event_id: str) -> Dict[str, Any]:
    """``cio_agent_flow`` on the zone's event, as TCB's agent_worker runs it."""
    from operonx import Operon

    from views.graph import cio_agent_flow

    engine = Operon(cio_agent_flow, params={"event_id": None, "by": None, "mode": None})
    out = await engine.run(inputs={"event_id": event_id, "by": ZONE_ACTOR, "mode": None})
    errors = out.get("$errors") or {}
    view_id = ((out.get("result") or {}).get("view") or {}).get("id")
    if errors:
        first = next(iter(errors.values()))
        return {"view_id": view_id, "error": str(first.get("reason") or first.get("message") or "lỗi")[:300]}
    return {"view_id": view_id, "error": None if view_id else "không ra nhận định"}


async def tick(now: Optional[float] = None, send: Optional[sync.Send] = None) -> Dict[str, Any]:
    """The ``zone_agent`` job (the AI zone only)."""
    if not in_zone():
        raise RuntimeError("zone_agent chạy trong vùng AI (MF_ZONE=on, app/zone.py)")
    resent = [deliver(oid, send)["status"] for oid in waiting()]
    if made_today(now) >= cap():
        return {"resent": resent, "made": None, "reason": f"Đã đủ {cap()} sự kiện hôm nay"}
    news = candidates(now)
    if not news:
        return {"resent": resent, "made": None, "reason": "Không có tin mới đủ liên quan"}
    ev = events.create([n["id"] for n in news], news[0]["title"], by=ZONE_ACTOR)
    got = await run_agent(ev["id"])
    v = vstore.get(got["view_id"]) if got["view_id"] else None
    if got["error"] or v is None or v["status"] != "PENDING_APPROVAL":
        why = got["error"] or (v or {}).get("challenge_error") or f"nhận định ở trạng thái {(v or {}).get('status')}"
        oid = _add(ev["id"], {"view_id": got["view_id"], "last_error": why, "attempts": 0}, "failed")
        return {"resent": resent, "made": {"id": oid, "event_id": ev["id"], "status": "failed", "error": why}}
    body = _body(package(v["id"]))
    oid = _add(
        ev["id"],
        {
            "view_id": v["id"],
            "package": body.decode("utf-8"),
            "attempts": 0,
            "package_hash": hashlib.sha256(body).hexdigest(),
            "mode": v["mode"],
        },
        "waiting",
    )
    out = deliver(oid, send)
    return {"resent": resent, "made": {k: out.get(k) for k in ("id", "event_id", "status", "tcb_id", "last_error")}}

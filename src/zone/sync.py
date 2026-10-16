"""TCB → the AI zone (ZONE-06): the approved catalogues and the released research, pushed by the ``zone_sync`` job in
inbox mode, signed with ``MF_ZONE_KEY`` (HMAC-SHA256, the inbox's scheme). Built from the kinds below and the research
items only, so nothing about a customer can go. Pushed again only when it changed."""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple

from control import audit, config, db
from inbox import sign
from news import store as news_store

VERSION = 1
KINDS = ("factor_model", "restricted", "forbidden_phrases", "news_sources", "prompts", "models")
NEWS_FIELDS = (  # what the zone keeps of a released research item (the news item it became at TCB)
    "source",
    "outlet",
    "section",
    "title",
    "summary",
    "url",
    "published",
    "ingested",
    "url_key",
    "title_key",
    "label",
    "kind",
    "factors",
    "relevance",
    "score",
    "event_type",
    "research_id",
    "report_no",
)

Send = Callable[[str, bytes, Dict[str, str]], Tuple[int, Dict[str, Any]]]


def zone_url() -> str:
    return (os.environ.get("MF_ZONE_URL") or "").strip().rstrip("/")


def zone_key() -> Optional[bytes]:
    k = (os.environ.get("MF_ZONE_KEY") or "").strip()
    return k.encode("utf-8") if k else None


def bundle() -> Dict[str, Any]:
    cats, not_set = {}, []
    for kind in KINDS:
        a = config.active(kind)
        try:
            config.KINDS[kind]["check"](a["data"])
        except ValueError:  # e.g. no models set for this deployment: the zone keeps its own (mock)
            not_set.append(kind)
            continue
        cats[kind] = {"id": a["id"], "hash": a["hash"], "data": a["data"]}
    research = [
        {k: it.get(k) for k in NEWS_FIELDS}
        for it in news_store.inbox(source="research", status="all", limit=1000)
        if it["status"] in ("new", "grouped") and not it["held"]
    ]
    return {"version": VERSION, "catalogues": cats, "not_set": not_set, "research": research}


def post(url: str, body: bytes, headers: Dict[str, str]) -> Tuple[int, Dict[str, Any]]:
    req = urllib.request.Request(url, data=body, method="POST", headers={"content-type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — the configured zone or TCB address
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"{}")
        except ValueError:
            return exc.code, {}


def last_ok() -> Optional[Dict[str, Any]]:
    with db.tx() as con:
        return db.load(con.execute("select * from zone_syncs where status = 'ok' order by at desc limit 1").fetchone())


def recent(limit: int = 10) -> list:
    with db.tx() as con:
        return [db.load(r) for r in con.execute("select * from zone_syncs order by at desc limit ?", (limit,))]


def push(send: Optional[Send] = None) -> Dict[str, Any]:
    """The ``zone_sync`` job: the bundle to the zone when it changed; skipped outside inbox mode or with no zone set."""
    from views import agents

    if agents.configured_mode() != "inbox":
        return {"status": "skipped", "reason": "Không ở chế độ hộp chờ"}
    url = zone_url()
    if not url:
        return {"status": "skipped", "reason": "Chưa đặt MF_ZONE_URL"}
    body = db.dumps(bundle()).encode("utf-8")
    h = hashlib.sha256(body).hexdigest()
    last = last_ok()
    if last and last["bundle_hash"] == h:
        return {"status": "unchanged", "id": last["id"]}
    key = zone_key()
    headers = {sign.HEADER: sign.sign(body, key)} if key else {}
    try:
        code, reply = (send or post)(url + "/api/zone/sync", body, headers)
    except Exception as exc:  # noqa: BLE001 — a zone that does not answer is a failed sync, tried again next time
        code, reply = 0, {"error": f"{type(exc).__name__}: {exc}"[:300]}
    status = "ok" if code == 200 else "failed"
    data = {
        "http": code,
        "applied": reply.get("applied", []),
        "research_added": reply.get("research_added", 0),
        "error": None if status == "ok" else str(reply.get("error") or f"HTTP {code}")[:300],
        "bytes": len(body),
    }
    with db.tx() as con:
        sid = f"ZS-{db.next_seq(con, 'zone_sync'):06d}"
        con.execute("insert into zone_syncs values (?, ?, ?, ?, ?)", (sid, time.time(), status, h, db.dumps(data)))
        audit.append(con, "system:zone_sync", "zone.sync", sid, {"status": status, "hash": h, **data})
    return {"id": sid, "status": status, **data}

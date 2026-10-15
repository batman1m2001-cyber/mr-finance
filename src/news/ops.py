"""The ingest steps: fetch every white-listed feed, pass each item through the gates, sort it,
keep it; and the inbox actions (dismiss, Compliance's release of a held item)."""

from __future__ import annotations

import asyncio
import json
import time
import urllib.request
from functools import lru_cache
from typing import Any, Dict, List, Optional

from operonx import op

from news import rss, rules, store
from wealth.paths import DATA

USER_AGENT = "OneWealth-demo/0.1 (+https://github.com/batman1m2001-cyber/mr-finance)"


@lru_cache(maxsize=1)
def config() -> Dict[str, Any]:
    """data/news_config.json (scripts/make_news_config.py): sources, words, the restricted list."""
    return json.loads((DATA / "news_config.json").read_text(encoding="utf-8"))


def _get(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — white-listed https URLs
        return resp.read(rss.MAX_BYTES + 1)


@op
async def fetch(feeds: Optional[dict] = None, now: Optional[float] = None) -> dict:
    """Every approved source's feed, at once. ``feeds`` ({source id: XML}) replaces the network
    (tests, replays); ``now`` the clock."""
    cfg = config()
    at = float(now) if now else time.time()
    sources = [s for s in cfg["sources"] if s.get("approved")]
    if feeds is not None:
        sources = [s for s in cfg["sources"] if s["id"] in feeds] + [
            {"id": sid, "url": "", "approved": False} for sid in feeds if rules.source_of(cfg, sid) is None
        ]

    async def one(src: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if feeds is not None:
                raw = feeds[src["id"]]
            else:
                raw = await asyncio.to_thread(_get, src["url"], cfg["gates"]["fetch_timeout_s"])
            items = rss.parse(raw)
            return {"source": src["id"], "items": [vars(i) for i in items], "error": None}
        except Exception as exc:  # noqa: BLE001 — one dead feed must not stop the others
            return {"source": src["id"], "items": [], "error": f"{type(exc).__name__}: {exc}"[:200]}

    fetched = await asyncio.gather(*(one(s) for s in sources))
    return {"fetched": list(fetched), "at": at}


@op
def screen(fetched: list, at: float) -> dict:
    """Each item through the gates; accepted items sorted, refused ones kept with the reason."""
    cfg = config()
    rows: List[Dict[str, Any]] = []
    counts: Dict[str, Dict[str, Any]] = {}
    for feed in fetched:
        sid = feed["source"]
        c = counts[sid] = {
            "fetched": len(feed["items"]),
            "accepted": 0,
            "refused": 0,
            "skipped": 0,
            "error": feed["error"],
        }
        for it in feed["items"]:
            v = rules.gate(cfg, sid, it["link"], it["published"], at)
            if v.outcome == rules.SKIP:
                c["skipped"] += 1
                continue
            base = {
                "source": sid,
                "title": it["title"],
                "summary": it["summary"],
                "url": it["link"],
                "published": it["published"],
                "ingested": at,
                "url_key": rules.url_key(it["link"] or it["guid"]),
                "title_key": rules.title_key(sid, it["title"]),
            }
            if v.outcome == rules.REFUSE:
                c["refused"] += 1
                rows.append({**base, "status": "refused", "refused_reason": v.reason})
                continue
            s = rules.classify(cfg, sid, it["title"], it["summary"])
            src = rules.source_of(cfg, sid)
            c["accepted"] += 1
            rows.append(
                {
                    **base,
                    "status": "new",
                    "outlet": src["outlet"],
                    "section": src["section"],
                    "label": "Quốc tế" if s.kind == "intl" else "Trong nước",
                    "kind": s.kind,
                    "factors": s.factors,
                    "relevance": s.relevance,
                    "score": s.score,
                    "event_type": s.event_type,
                    "restricted": s.restricted,
                }
            )
    return {"rows": rows, "counts": counts}


@op
def keep(rows: list, counts: dict, at: float) -> dict:
    """The new items kept, and the run recorded for the feed-health strip."""
    kept, dup = store.add(rows)
    added = [r["id"] for r in kept if r["status"] == "new"]
    summary = {
        "at": at,
        "added": len(added),
        "refused": len(kept) - len(added),
        "duplicates": dup,
        "held": sum(1 for r in kept if r["status"] == "new" and r.get("restricted")),
        "sources": counts,
    }
    store.record_run(summary)
    return {"ingest": {**summary, "ids": added}}


@op
def dismiss(ids: list, by: str = "cio", note: str = "") -> dict:
    """The CIO drops items from the inbox (FR-103)."""
    return {"changed": store.set_status([str(i) for i in ids], "dismissed", by=by, note=note)}


@op
def release(item_id: str, by: str, note: str) -> dict:
    """Compliance releases a held item; the note is required, and kept with who and when."""
    if not str(note or "").strip():
        raise ValueError("Cần ghi chú lý do cho phép")
    if not store.clear_hold(str(item_id), by=str(by), note=str(note).strip()):
        raise ValueError(f"{item_id} không bị giữ")
    return {"released": str(item_id)}

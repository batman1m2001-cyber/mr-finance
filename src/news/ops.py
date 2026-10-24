"""The ingest steps: fetch every white-listed feed, pass each item through the gates, sort it,
keep it; and the inbox actions (dismiss, the release of a held item)."""

from __future__ import annotations

import asyncio
import ipaddress
import json
import socket
import time
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Any, Dict, List, Optional

from operonx import op

from control import alerts, roles
from news import rss, rules, store
from people import auth
from wealth.paths import DATA

USER_AGENT = "OneWealth-demo/0.1 (+https://github.com/batman1m2001-cyber/mr-finance)"


@lru_cache(maxsize=1)
def _file() -> Dict[str, Any]:
    return json.loads((DATA / "news_config.json").read_text(encoding="utf-8"))


def config() -> Dict[str, Any]:
    """data/news_config.json (scripts/make_news_config.py): sources, words, the restricted list — with the
    sources and the restricted list as their approved versions in force (FR-701)."""
    from control import config as versioned

    return {**_file(), "sources": versioned.data("news_sources"), "restricted": versioned.data("restricted")}


def _get(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 — white-listed https URLs
        return resp.read(rss.MAX_BYTES + 1)


def _public(url: str) -> str:
    """The host of an https ``url`` whose every address is public, or ValueError (the Nguồn tin test, N1)."""
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or not u.hostname:
        raise ValueError("chỉ thử url https")
    try:
        addrs = {a[4][0] for a in socket.getaddrinfo(u.hostname, u.port or 443, proto=socket.IPPROTO_TCP)}
    except OSError as exc:
        raise ValueError(f"không tìm thấy máy chủ {u.hostname}: {exc}") from None
    for a in addrs:
        ip = ipaddress.ip_address(a.split("%", 1)[0])
        if not ip.is_global or ip.is_multicast:
            raise ValueError(f"{u.hostname} trỏ về địa chỉ nội bộ {ip}: không thử")
    return u.hostname


class _Checked(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _public(newurl)  # a redirect may not lead inside either
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def probe(url: str) -> Dict[str, Any]:
    """Read one feed now, keep nothing: its item count and newest title, or why it failed (N1)."""
    t0 = time.time()
    try:
        _public(url)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        timeout = float(config()["gates"]["fetch_timeout_s"])
        with urllib.request.build_opener(_Checked).open(req, timeout=timeout) as resp:
            items = rss.parse(resp.read(rss.MAX_BYTES + 1))
    except Exception as exc:  # noqa: BLE001 — the answer is the reason, for the Admin
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:300], "ms": round((time.time() - t0) * 1000)}
    newest = max(items, key=lambda i: i.published or 0, default=None)
    return {
        "ok": True,
        "items": len(items),
        "newest": {"title": newest.title, "published": newest.published} if newest else None,
        "ms": round((time.time() - t0) * 1000),
    }


@op
async def fetch(feeds: Optional[dict] = None, now: Optional[float] = None) -> dict:
    """Every approved source's feed, at once. ``feeds`` ({source id: XML}) replaces the network
    (tests, replays); ``now`` the clock. Asked over HTTP, only the CIO fetches, and from the network.

    The scheduled job runs without a request."""
    if auth.checking():
        roles.require_signed_in("cio")
        feeds, now = None, None  # a caller does not supply the news
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

    started = time.time()
    fetched = await asyncio.gather(*(one(s) for s in sources))
    return {"fetched": list(fetched), "at": at, "started": started}


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


NO_TIME = "Tin không có giờ công bố"  # rules.gate's reason


def run_summary(
    kept: List[Dict[str, Any]], dup: int, counts: Dict[str, Any], at: float, started: Optional[float] = None
) -> Dict[str, Any]:
    """The run's record (AGENT_EVALUATION_PLAN §2.1). The funnel: fetched = too old + duplicates + unique;
    unique = refused + retained; relevant ⊆ retained, the agents' candidate rule (medium or high, not restricted).
    ``at`` is the collection time every item gets as ``ingested``; ``started``/``finished`` the wall clock."""
    from trial import segments

    finished = time.time()
    retained = [r for r in kept if r["status"] == "new"]
    attempted = len(counts)
    failed = sorted(sid for sid, c in counts.items() if c.get("error"))
    configured = sum(1 for s in config()["sources"] if s.get("approved"))
    fetched = sum(int(c.get("fetched") or 0) for c in counts.values())
    skipped = sum(int(c.get("skipped") or 0) for c in counts.values())
    by_category: Dict[str, int] = {k: 0 for k in (*segments.FAMILIES, "unclassified")}
    for r in retained:
        by_category[segments.family_of_item(r) or "unclassified"] += 1
    return {
        "at": at,
        "started": started,
        "finished": finished,
        "duration_s": round(finished - started, 2) if started else None,
        "status": "failed" if attempted == 0 or len(failed) == attempted else "partial" if failed else "ok",
        "configured": configured,
        "attempted": attempted,
        "succeeded": attempted - len(failed),
        "failed": len(failed),
        "failed_sources": {sid: counts[sid]["error"] for sid in failed},
        "fetched": fetched,
        "skipped": skipped,
        "duplicates": dup,
        "unique": len(kept),
        "added": len(retained),  # the inbox's new items: “retained” (the strip has read “added” since FEAT-01)
        "retained": len(retained),
        "refused": len(kept) - len(retained),
        "relevant": sum(1 for r in retained if r.get("relevance") in ("high", "medium") and not r.get("restricted")),
        "held": sum(1 for r in retained if r.get("restricted")),
        "by_category": by_category,
        "missing": {
            "published": sum(1 for r in kept if r.get("refused_reason") == NO_TIME),
            "summary": sum(1 for r in retained if not (r.get("summary") or "").strip()),
            "category": by_category["unclassified"],
        },
        "sources": counts,
    }


@op
def keep(rows: list, counts: dict, at: float, started: Optional[float] = None) -> dict:
    """The new items kept, and the run recorded: the feed-health strip and the collection monitor."""
    kept, dup = store.add(rows)
    for sid, c in counts.items():  # a feed that failed raises an alert; one that answered resolves it (NFR-12)
        if c.get("error"):
            alerts.raise_("news_feed", sid, f"Nguồn tin {sid} không lấy được", c["error"])
        else:
            alerts.resolve("news_feed", sid)
    added = [r["id"] for r in kept if r["status"] == "new"]
    summary = run_summary(kept, dup, counts, at, started)
    store.record_run(summary)
    return {"ingest": {**summary, "ids": added}}


@op
def dismiss(ids: list, by: str = "cio", note: str = "") -> dict:
    """The CIO drops items from the inbox (FR-103)."""
    roles.require(by, "cio")
    return {"changed": store.set_status([str(i) for i in ids], "dismissed", by=by, note=note)}


@op
def release(item_id: str, by: str, note: str) -> dict:
    """The CIO releases a held item (Compliance's step before OWN-FB-18); the note is required, and kept with who
    and when."""
    roles.require(by, "cio")
    if not str(note or "").strip():
        raise ValueError("Cần ghi chú lý do cho phép")
    if not store.clear_hold(str(item_id), by=str(by), note=str(note).strip()):
        raise ValueError(f"{item_id} không bị giữ")
    return {"released": str(item_id)}


@op
async def reference_check(feed: Optional[str] = None, now: Optional[float] = None) -> dict:
    """The ``news_reference`` job (BRD-KPI-02, news/reference.py): the independent reference read (``feed`` replaces
    the network), its stories kept, the ones a day old judged collected or not. A reference that cannot be read
    raises a feed alert; reading again resolves it."""
    from control import alerts
    from news import reference

    ref = config()["reference"]
    at = float(now) if now else time.time()
    try:
        raw = (
            feed
            if feed is not None
            else await asyncio.to_thread(_get, ref["url"], config()["gates"]["fetch_timeout_s"])
        )
        stories = reference.parse(raw)
    except Exception as exc:  # noqa: BLE001 — recorded and alerted, the next run tries again
        alerts.raise_("news_feed", "reference", f"Không đọc được nguồn đối chiếu {ref['outlet']}", str(exc)[:300])
        return {
            "error": f"{type(exc).__name__}: {exc}"[:200],
            "stories": 0,
            "added": 0,
            "grown": 0,
            "judged": reference.judge(at),
        }
    alerts.resolve("news_feed", "reference", f"Đọc lại được nguồn đối chiếu ({len(stories)} tin)")
    kept = reference.keep(stories, at)
    return {
        "error": None,
        "stories": len(stories),
        "added": kept["added"],
        "grown": kept["grown"],
        "judged": reference.judge(at),
    }

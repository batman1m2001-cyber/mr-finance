"""The import (BRD-RULE-ZONE-03, AI-13 inbox mode): each READY package through the checks a live run passes, in
order, before anything is written:

1. signed, when ``MF_INBOX_KEY`` is set (LC-04);
2. the package's form (version, event, 1–8 news, view, challenge, run);
3. every news item is one TCB fetched itself from a white-listed source, or research TCB released — matched by its
   address, never taken from the package (FR-104) — still in the inbox, and not held for the restricted list
   (FR-105). A news item TCB has not fetched yet keeps the package READY for up to an hour (the two sides fetch on
   their own clocks);
4. the view passes the format check (§8.2, AI-05, the impacts and branches' sources belong to the event);
5. the challenge's findings are well formed.

Then: the event, the view waiting for the challenge, the AI zone's run trace (mode ``inbox``), the challenge —
the rules run here again, on top of the zone's model findings — and the view waits for the CIO. A rejected package
changes nothing and keeps its error.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from control import alerts
from events import store as events
from inbox import sign, store
from news import rules
from news import store as news_store
from news.ops import config as news_config
from views import challenger, schema
from views import store as vstore

VERSION = 1
WAIT_FOR_NEWS_S = 3600
BY = "agent:zone"


class Rejected(Exception):
    """The package fails a check: REJECTED with this error."""


class NotYet(Exception):
    """A news item TCB has not fetched yet: READY again."""


def run_ready() -> List[Dict[str, Any]]:
    """The ``inbox_import`` job: every READY package, oldest first."""
    return [import_one(row) for row in store.ready()]


def import_one(row: Dict[str, Any]) -> Dict[str, Any]:
    pid = row["id"]
    store.mark(pid, "PROCESSING")
    try:
        got = _import(row)
    except NotYet as exc:
        store.mark(pid, "READY", waiting=str(exc))
        return {"id": pid, "status": "READY", "waiting": str(exc)}
    except Rejected as exc:
        return _reject(pid, str(exc))
    except Exception as exc:  # noqa: BLE001 — a package that breaks the import is refused, not left PROCESSING
        return _reject(pid, f"{type(exc).__name__}: {exc}"[:500])
    store.mark(pid, "IMPORTED", **got)
    return {"id": pid, "status": "IMPORTED", **got}


def _reject(pid: str, why: str) -> Dict[str, Any]:
    store.mark(pid, "REJECTED", error=why)
    alerts.raise_("inbox", pid, f"Gói {pid} từ vùng AI bị từ chối", why)
    return {"id": pid, "status": "REJECTED", "error": why}


def _import(row: Dict[str, Any]) -> Dict[str, Any]:
    if sign.key() and not row["signed"]:
        raise Rejected("Gói chưa ký hoặc chữ ký sai (MF_INBOX_KEY)")
    try:
        pkg = json.loads(row["body"])
    except ValueError as exc:
        raise Rejected(f"Không đọc được JSON: {exc}") from None
    _form(pkg)
    refs = _news(pkg["news"], row["received"])
    view = _remap(pkg["view"], refs)
    errs = schema.check(view, list(refs.values()), agent=True)
    if errs:
        raise Rejected("Nhận định sai định dạng: " + "; ".join(errs[:5]))
    model_findings = _findings(pkg["challenge"])
    run = pkg["run"]
    models = {"cio": str(run["models"]["cio"])[:120], "challenger": str(run["models"]["challenger"])[:120]}

    # every check passed: write
    ev = events.create(list(dict.fromkeys(refs.values())), str(pkg["event"]["title"])[:200], by=BY)
    rec = vstore.create(ev["id"], BY, "inbox", models)
    run_id = vstore.start_run("cio", rec["id"], "inbox", models["cio"])
    for node in run.get("nodes", [])[:60]:
        vstore.add_node(run_id, {**node, "zone_mode": node.get("mode"), "mode": "inbox"})
    from views.ops import keep_draft

    keep_draft(rec["id"], run_id, view, [], BY, f"Nhận từ vùng AI qua hộp chờ ({row['id']})")
    v = vstore.get(rec["id"])
    ch_run = vstore.start_run("challenger", rec["id"], "inbox", models["challenger"])
    found = challenger.findings(v["current"], ev) + model_findings
    vstore.finish_run(ch_run, "ok")
    ch = vstore.add_challenge(
        rec["id"],
        "pre_approval",
        {
            "findings": found,
            "model": models["challenger"],
            "mode": "inbox",
            "content_hash": v["content_hash"],
            "independent": models["challenger"] != models["cio"],
            "run_id": ch_run,
        },
    )
    vstore.save(v, "PENDING_APPROVAL", BY, f"Phản biện {ch['id']}: {len(found)} phát hiện")
    return {"event_id": ev["id"], "view_id": rec["id"], "zone_run": pkg.get("zone_run"), "zone_mode": run["mode"]}


def _form(pkg: Any) -> None:
    if not isinstance(pkg, dict) or pkg.get("version") != VERSION:
        raise Rejected(f"Gói phải là đối tượng JSON, version {VERSION}")
    ev, news, run = pkg.get("event"), pkg.get("news"), pkg.get("run")
    if not isinstance(ev, dict) or not str(ev.get("title") or "").strip():
        raise Rejected("event.title: cần tiêu đề sự kiện")
    if not isinstance(news, list) or not 1 <= len(news) <= 8:
        raise Rejected("news: cần 1–8 tin")
    for n in news:
        if not isinstance(n, dict) or not all(isinstance(n.get(k), str) and n[k] for k in ("ref", "url", "source")):
            raise Rejected("news[]: mỗi tin cần ref, url, source")
    if not isinstance(pkg.get("view"), dict) or not isinstance(pkg.get("challenge"), dict):
        raise Rejected("view và challenge: cần đối tượng")
    if not isinstance(run, dict) or run.get("mode") not in ("live", "mock"):
        raise Rejected("run.mode: live hoặc mock")
    m = run.get("models")
    if not isinstance(m, dict) or not all(isinstance(m.get(k), str) and m[k] for k in ("cio", "challenger")):
        raise Rejected("run.models: cần cio và challenger")
    if not isinstance(run.get("nodes", []), list):
        raise Rejected("run.nodes: cần danh sách")


def _news(items: List[Dict[str, Any]], received: float) -> Dict[str, str]:
    cfg = news_config()
    refs: Dict[str, str] = {}
    for n in items:
        if n["source"] == "research":  # research TCB released and synced to the zone (ZONE-06), by its id
            key = "research/" + n["url"].split("://", 1)[-1]
        else:
            src = rules.source_of(cfg, n["source"])
            if src is None or not src.get("approved"):
                raise Rejected(f"Nguồn {n['source']!r} không nằm trong danh sách trắng")
            key = rules.url_key(n["url"])
        item = news_store.by_url_key(key)
        if item is None:
            if time.time() - received < WAIT_FOR_NEWS_S:
                raise NotYet(f"TCB chưa lấy tin {n['url']}")
            raise Rejected(f"Tin không có trong hộp tin của TCB sau 1 giờ: {n['url']}")
        if item.get("source") != n["source"]:
            raise Rejected(f"Tin {n['url']} thuộc nguồn {item.get('source')!r}, không phải {n['source']!r}")
        if item["held"]:
            raise Rejected(f"Tin {item['id']} nhắc tới danh sách hạn chế: Tuân thủ xem trong Hộp tin")
        if item["status"] not in ("new", "grouped"):
            raise Rejected(f"Tin {item['id']} đã bị bỏ hoặc bị từ chối")
        refs[n["ref"]] = item["id"]
    return refs


def _remap(view: Dict[str, Any], refs: Dict[str, str]) -> Dict[str, Any]:
    """The view with the package's news references replaced by TCB's ids (a reference the package did not list is
    left as it is, and the format check refuses it)."""

    def walk(x: Any) -> Any:
        if isinstance(x, dict):
            return {
                k: ([refs.get(i, i) for i in v] if k == "source_ids" and isinstance(v, list) else walk(v))
                for k, v in x.items()
            }
        if isinstance(x, list):
            return [walk(i) for i in x]
        return x

    return walk(view)


def _findings(ch: Dict[str, Any]) -> List[Dict[str, Any]]:
    got = ch.get("findings", [])
    if not isinstance(got, list):
        raise Rejected("challenge.findings: cần danh sách")
    out = []
    for i, f in enumerate(got):
        if not isinstance(f, dict) or f.get("severity") not in schema.SEVERITIES or not f.get("title"):
            raise Rejected(f"challenge.findings[{i}]: cần severity ({', '.join(schema.SEVERITIES)}) và title")
        if f.get("source") == "rule":
            continue  # the rules run here again
        out.append(
            {
                "id": f"Z{len(out) + 1}",
                "severity": f["severity"],
                "title": str(f["title"])[:200],
                "detail": str(f.get("detail", ""))[:1000],
                "target": str(f.get("target", ""))[:100],
                "source": "zone",
            }
        )
    return out

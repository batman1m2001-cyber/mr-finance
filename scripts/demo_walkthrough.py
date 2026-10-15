"""Fill the demo through the served flows, over HTTP, the way the CIO would (UI redesign R6, OWN-UI-06).

    python scripts/demo_walkthrough.py [--base http://localhost:8030] [--events 3] [--pending 1] [--dry-run]

1. POST /api/news/ingest — fetch the whitelisted feeds now.
2. GET /api/news/inbox — the news that passed the gates; the event types with the most news, not held.
3. For each of them: POST /api/events (the newest news of that type, at most four), POST /api/events/run-agent (the CIO
   agent, then the challenger — live models when the server has them, else the labelled mock), and, except for the
   last ``--pending`` events, which stay for the CIO screen: answer each critical finding and approve
   (POST /api/views/decide), which applies the view to every family.

Every decision this script takes says so in its reason (“kịch bản demo tự động”), in the audit chain like any other.
It never edits a view. A step that fails is printed and the next event goes on.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict

BY = "cio"
WHO = "kịch bản demo tự động (scripts/demo_walkthrough.py)"


def call(base: str, path: str, body: dict | None = None, timeout: float = 600) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, headers={"content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = json.load(r)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"{path}: {exc.code} {exc.read().decode()[:300]}") from None
    if isinstance(out, dict) and "$errors" in out:
        err = next(iter(out["$errors"].values()))
        raise RuntimeError(f"{path}: {err.get('message') or err}")
    return out


def groups(items: list, n: int) -> list:
    """The event types with the most news (two or more), newest news first, at most four per event."""
    by: dict = defaultdict(list)
    for it in items:
        if it.get("held") or not it.get("event_type"):
            continue
        by[it["event_type"]].append(it)
    ranked = sorted((v for v in by.values() if len(v) >= 2), key=lambda v: (-len(v), -max(x["published"] for x in v)))
    return [sorted(v, key=lambda x: -x["published"])[:4] for v in ranked[:n]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://localhost:8030")
    ap.add_argument("--events", type=int, default=3)
    ap.add_argument("--pending", type=int, default=1, help="the last N events stay pending for the CIO screen")
    ap.add_argument("--dry-run", action="store_true", help="fetch and print the planned events, change nothing else")
    a = ap.parse_args()
    base = a.base.rstrip("/")

    status = call(base, "/api/agents")
    m, b = status["models"], status["budget"]
    print(f"Agent: chế độ {status.get('mode')} · CIO {m.get('cio')} · phản biện {m.get('challenger')}")
    print(f"Ngân sách: {b.get('used_today')}/{b.get('daily')} token hôm nay")
    got = call(base, "/api/news/ingest", {})["ingest"]
    print(f"Ingest: +{got['added']} tin, bỏ {got['refused']}, trùng {got['duplicates']}, giữ {got['held']}")
    inbox = call(base, "/api/news/inbox?limit=500")
    items = inbox.get("items") or inbox.get("inbox") or []
    plan = groups(items, a.events)
    if not plan:
        print("Không có loại tin nào đủ hai tin mới để gom thành sự kiện.")
        return 0
    for k, news in enumerate(plan):
        print(f"\n[{k + 1}/{len(plan)}] {news[0]['event_type']}: " + " | ".join(n["title"][:60] for n in news))
    if a.dry_run:
        return 0

    approve_upto = max(0, len(plan) - a.pending)
    for k, news in enumerate(plan):
        tag = f"[{k + 1}/{len(plan)}]"
        try:
            ev = call(base, "/api/events", {"news_ids": [n["id"] for n in news], "by": BY})["event"]
            t0 = time.time()
            res = call(base, "/api/events/run-agent", {"event_id": ev["id"], "by": BY})["result"]
            view = res["view"]
            print(
                f"{tag} {ev['id']} → {view['id']} ({view['status']}, {time.time() - t0:.0f} s, "
                f"mode {(res.get('agent') or {}).get('mode') or view.get('mode') or '?'})"
            )
            if k >= approve_upto:
                print(f"{tag} để chờ CIO duyệt")
                continue
            pub = call(base, f"/api/views/{view['id']}")
            ch = (pub.get("challenges") or [None])[-1]
            critical = [f for f in (ch or {}).get("findings", []) if f["severity"] == "critical"]
            if critical:
                responses = {f["id"]: {"decision": "accept", "reason": f"Ghi nhận phát hiện; {WHO}"} for f in critical}
                call(
                    base,
                    "/api/views/decide",
                    {"view_id": view["id"], "action": "respond", "by": BY, "responses": responses},
                )
                print(f"{tag} trả lời {len(critical)} phát hiện nghiêm trọng")
            dec = call(
                base,
                "/api/views/decide",
                {
                    "view_id": view["id"],
                    "action": "approve",
                    "by": BY,
                    "reason": f"Duyệt bởi {WHO}",
                    "idem_key": f"demo-{view['id']}",
                },
            )
            run = (dec.get("decision") or {}).get("run") or {}
            print(f"{tag} duyệt → lần áp dụng {run.get('id')} ({run.get('status_label')})")
        except RuntimeError as exc:
            print(f"{tag} lỗi: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

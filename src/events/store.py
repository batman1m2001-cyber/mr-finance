"""Events, kept: ``EV-2026-0007``, the news they group, who grouped them, and whether they are held.

An event is held (``blocked``) while any of its news names someone on the restricted list and
Compliance has not released it (BR-04); this is read from the news, so a release unblocks at once.
"""

from __future__ import annotations

import time
from collections import Counter
from typing import Any, Dict, List, Optional

from control import audit, db
from news import store as news_store


class EventError(ValueError):
    pass


def create(news_ids: List[str], title: Optional[str], by: str) -> Dict[str, Any]:
    items = news_store.get(news_ids)
    missing = sorted(set(news_ids) - {i["id"] for i in items})
    if missing:
        raise EventError(f"không có tin {', '.join(missing)}")
    bad = [i["id"] for i in items if i["status"] not in ("new", "grouped")]
    if bad:
        raise EventError(f"tin {', '.join(bad)} đã bị bỏ hoặc bị từ chối")
    types = Counter(i.get("event_type") for i in items if i.get("event_type"))
    now = time.time()
    year = time.strftime("%Y", time.localtime(now))
    data = {
        "title": (title or items[0]["title"]).strip()[:200],
        "news_ids": [i["id"] for i in items],
        "type": types.most_common(1)[0][0] if types else None,
        "created_by": by,
        "factors": sorted({f for i in items for f in i.get("factors", [])}),
        "kinds": sorted({i.get("kind") for i in items if i.get("kind")}),
    }
    with db.tx() as con:
        seq = db.next_seq(con, f"event-{year}")
        event_id = f"EV-{year}-{seq:04d}"
        con.execute("insert into events values (?, ?, ?, ?)", (event_id, now, "open", db.dumps(data)))
        audit.append(con, by, "event.create", event_id, {"news_ids": data["news_ids"], "title": data["title"]})
    news_store.set_status(data["news_ids"], "grouped", by=by, note=event_id)
    return get(event_id)


def get(event_id: str) -> Dict[str, Any]:
    with db.tx() as con:
        ev = db.load(con.execute("select * from events where id = ?", (event_id,)).fetchone())
    if ev is None:
        raise EventError(f"không có sự kiện {event_id}")
    ev["news"] = news_store.get(ev["news_ids"])
    ev["held"] = [i["id"] for i in ev["news"] if i["held"]]
    ev["blocked"] = bool(ev["held"])
    return ev


def listing() -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from events order by created desc").fetchall()
    return [get(r["id"]) for r in rows]

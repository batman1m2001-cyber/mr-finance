"""Research items: a report, a house view or a regulation note, uploaded by the research side and
released (or rejected) by a second CIO (FR-201…204, BR-03, F13).

- Release needs: a CIO other than the uploader (separation of duties), a note of at
  least 20 characters, the release time reached (nothing is read before it is public), no mention
  of the restricted list, and — for a regulation note — no forbidden wording (FR-604).
- A released report or house view enters the CIO's inbox as an exclusive news item; a regulation
  note goes to the goal branch only, never into a price event (FR-204).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from control import audit, db
from news import rules
from news import store as news_store
from news.ops import config as news_config
from procedural import goals

KINDS = {"research": "Báo cáo nghiên cứu", "house_view": "House view", "regulation": "Ghi chú quy định"}


class ResearchError(ValueError):
    pass


def _ts(text: str) -> float:
    try:
        dt = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        raise ResearchError("release_at: thời điểm ISO, ví dụ 2026-10-15T08:00:00+07:00") from None
    if dt.tzinfo is None:
        raise ResearchError("release_at cần múi giờ (ví dụ +07:00)")
    return dt.astimezone(timezone.utc).timestamp()


def _conflict(item: Dict[str, Any]) -> Dict[str, Any]:
    from research import conflict

    try:
        given = item.get("conflict", item.get("conflicts"))
        return conflict.declare(given, item.get("title", ""), item.get("summary", ""))
    except conflict.ConflictError as exc:
        raise ResearchError(str(exc)) from None


def upload(item: Dict[str, Any], by: str) -> Dict[str, Any]:
    kind = item.get("kind")
    if kind not in KINDS:
        raise ResearchError(f"kind là một trong {', '.join(KINDS)}")
    for f in ("report_no", "title", "summary", "release_at"):
        if not str(item.get(f) or "").strip():
            raise ResearchError(f"thiếu {f}")
    data = {
        "kind": kind,
        "report_no": str(item["report_no"]).strip(),
        "title": str(item["title"]).strip(),
        "summary": str(item["summary"]).strip(),
        "release_at": _ts(item["release_at"]),
        "conflict": _conflict(item),
        "uploaded_by": by,
        "history": [{"at": time.time(), "by": by, "status": "PENDING_RELEASE", "note": ""}],
    }
    if kind == "regulation":
        reg = dict(item.get("regulation") or {})
        purposes = [p for p in reg.get("purposes", []) if p in goals.PURPOSES]
        if not purposes:
            raise ResearchError(f"regulation.purposes: một hay nhiều trong {', '.join(goals.PURPOSES)}")
        if reg.get("status") not in ("draft", "issued"):
            raise ResearchError("regulation.status là draft hoặc issued")
        bad = goals.forbidden_words(reg.get("client_message", ""), reg.get("rm_hint", ""))
        if bad:
            raise ResearchError(f"Thông điệp không được nhắc: {', '.join(bad)} (FR-604)")
        data["regulation"] = {
            "document": str(reg.get("document") or data["title"]),
            "status": reg["status"],
            "effective_date": reg.get("effective_date"),
            "purposes": purposes,
            "countries": list(reg.get("countries") or []),
            "prep_weeks": int(reg.get("prep_weeks") or 0),
            "documents": list(reg.get("documents") or []),
            "client_message": str(reg.get("client_message") or ""),
            "rm_hint": str(reg.get("rm_hint") or ""),
        }
    with db.tx() as con:
        seq = db.next_seq(con, "research")
        rid = f"RS-{seq:04d}"
        con.execute(
            "insert into research_items values (?, ?, ?, ?, ?)",
            (rid, kind, "PENDING_RELEASE", time.time(), db.dumps(data)),
        )
        audit.append(con, by, "research.upload", rid, {"kind": kind, "report_no": data["report_no"]})
    return get(rid)


def decide(rid: str, decision: str, by: str, note: str, now: Optional[float] = None) -> Dict[str, Any]:
    item = get(rid)
    if item["status"] != "PENDING_RELEASE":
        raise ResearchError(f"{rid} đã {item['status']}")
    if by == item["uploaded_by"]:
        raise ResearchError("Người phát hành phải khác người nạp: cần một CIO khác")
    note = str(note or "").strip()
    if len(note) < 20:
        raise ResearchError("Ghi chú phát hành cần từ 20 ký tự")
    if decision == "release":
        if (now or time.time()) < item["release_at"]:
            raise ResearchError("Chưa tới giờ phát hành: không nạp trước khi công bố")
        cfg = news_config()
        hit = rules.classify(cfg, "research", item["title"], item["summary"]).restricted
        if hit:
            raise ResearchError(f"Nhắc tới danh sách hạn chế: {', '.join(hit)}")
        status = "RELEASED"
    elif decision == "reject":
        status = "REJECTED"
    else:
        raise ResearchError("decision là release hoặc reject")
    with db.tx() as con:
        row = con.execute("select data from research_items where id = ?", (rid,)).fetchone()
        data = json.loads(row["data"])
        data["history"].append({"at": time.time(), "by": by, "status": status, "note": note})
        data["decided_by"] = by
        con.execute("update research_items set status = ?, data = ? where id = ?", (status, db.dumps(data), rid))
        audit.append(con, by, f"research.{decision}", rid, {"note": note})
    if status == "RELEASED" and item["kind"] != "regulation":
        _to_inbox(get(rid))
    return get(rid)


def _to_inbox(item: Dict[str, Any]) -> None:
    """A released report or house view: an exclusive item in the CIO's inbox, published at release."""
    s = rules.classify(news_config(), "research", item["title"], item["summary"])
    news_store.add(
        [
            {
                "source": "research",
                "outlet": "Nghiên cứu nội bộ",
                "section": KINDS[item["kind"]],
                "title": item["title"],
                "summary": item["summary"],
                "url": f"research://{item['id']}",
                "published": item["release_at"],
                "ingested": time.time(),
                "status": "new",
                "url_key": f"research/{item['id']}",
                "title_key": rules.title_key("research", item["title"]),
                "label": "Độc quyền",
                "kind": "exclusive",
                "factors": s.factors,
                "relevance": s.relevance,
                "score": s.score,
                "event_type": s.event_type,
                "restricted": [],
                "research_id": item["id"],
                "report_no": item["report_no"],
                "conflict": item.get("conflict"),
            }
        ]
    )


def get(rid: str) -> Dict[str, Any]:
    with db.tx() as con:
        r = db.load(con.execute("select * from research_items where id = ?", (rid,)).fetchone())
    if r is None:
        raise KeyError(f"không có {rid}")
    if "conflict" not in r:  # kept before the field was structured (F8): the free text is the statement
        text = str(r.get("conflicts") or "").strip()
        r["conflict"] = {
            "related": bool(text) and text.lower() not in ("không", "không có"),
            "parties": [],
            "statement": text,
            "mentions": [],
        }
    return r


def listing(status: Optional[str] = None) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute(
            "select * from research_items" + (" where status = ?" if status else "") + " order by created desc",
            (status,) if status else (),
        ).fetchall()
    return [db.load(r) for r in rows]


def released_notes() -> List[Dict[str, Any]]:
    return [r for r in listing("RELEASED") if r["kind"] == "regulation"]


# -- the RM's declarations: a goal's outflow purpose and destination (FR-601) --------------------


def declare(family_id: str, goal_id: str, purpose: str, country: str, by: str) -> Dict[str, Any]:
    if purpose not in goals.PURPOSES:
        raise ResearchError(f"purpose là một trong {', '.join(goals.PURPOSES)}")
    data = {"purpose": purpose, "country": str(country or "").strip(), "by": by, "at": time.time()}
    with db.tx() as con:
        con.execute(
            "insert or replace into goal_outflows values (?, ?, ?, ?)",
            (goal_id, family_id, time.time(), db.dumps(data)),
        )
        audit.append(con, by, "goal.declare", goal_id, {"family_id": family_id, **data})
    return {"goal_id": goal_id, "family_id": family_id, **data}


def declared() -> Dict[str, Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select goal_id, data from goal_outflows").fetchall()
    return {r["goal_id"]: json.loads(r["data"]) for r in rows}

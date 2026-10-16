"""The RM's contact log (BRD-KPI-06 “liên hệ bắt đầu từ tín hiệu hệ thống ≥ 50%”; BRD_REMAINING_PLAN G7).

An RM records each contact with a family: when, how (a call, a meeting, a message), a note, and the system
signal it started from, or none (the RM's own initiative). A signal is one of the RM's Hôm nay rows:

- ``pre_review:<run>`` — the family was flagged for pre-review by that application run;
- ``goal:<note>:<goal>`` — a released regulation note applies to one of the family's goals.

The signal is checked when the contact is recorded: the run must have flagged that family, the note must still
apply to that goal. So the share counts only signals the product really gave. Each contact is audited
(``contact.log``); the note is client data and sealed at rest like the other client columns (control/crypto.py).
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from control import audit, crypto, db
from control.errors import BadRequest

CHANNELS = {"call": "Gọi điện", "meeting": "Gặp mặt", "message": "Tin nhắn"}
TARGET = 0.5  # BRD-KPI-06


def _aad(cid: str) -> bytes:
    return crypto.where("rm_contacts", cid, "data")


def signal(family_id: str, signal_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """The signal ``signal_id`` as the product gave it for ``family_id``; BadRequest when it never did."""
    if not signal_id:
        return None
    from measure import control

    if control.is_control(family_id):
        raise BadRequest(f"Gia đình {family_id} thuộc nhóm đối chứng: hệ thống không đưa tín hiệu nào cho gia đình này")
    kind, _, rest = str(signal_id).partition(":")
    if kind == "pre_review":
        from apply import run as runs

        try:
            r = runs.get(rest)
        except KeyError:
            r = None
        if r is not None and r["status"] not in runs.RM_VISIBLE:  # the RM never saw it
            r = None
        row = next((x for x in (r or {}).get("ranking", []) if x["family_id"] == family_id and x["pre_review"]), None)
        if row is None:
            raise BadRequest(f"Lần áp dụng {rest} không đưa gia đình {family_id} vào danh sách xem trước")
        ev = r.get("event_id")
        return {"id": signal_id, "kind": "pre_review", "label": f"Xem trước sau {rest} ({ev})"}
    if kind == "goal":
        from research.ops import matches

        note, _, goal = rest.partition(":")
        m = next((x for x in matches(family_id) if x["note_id"] == note and x["goal_id"] == goal), None)
        if m is None:
            raise BadRequest(f"Ghi chú {note} không áp dụng cho mục tiêu {goal} của gia đình {family_id}")
        return {"id": signal_id, "kind": "goal", "label": f"{m['goal']}: {m['note_title']}"}
    raise BadRequest("Tín hiệu là pre_review:<lần áp dụng> hoặc goal:<ghi chú>:<mục tiêu>")


def log(family_id: str, channel: str, signal_id: Optional[str], note: str, by: str) -> Dict[str, Any]:
    if channel not in CHANNELS:
        raise BadRequest(f"Cách liên hệ là một trong: {', '.join(CHANNELS)}")
    sig = signal(family_id, signal_id)
    now = time.time()
    with db.tx() as con:
        cid = f"CT-{db.next_seq(con, 'contact'):06d}"
        data = {"channel": channel, "note": str(note or "").strip()[:500], "signal": sig}
        con.execute(
            "insert into rm_contacts values (?, ?, ?, ?, ?, ?)",
            (
                cid,
                now,
                family_id,
                by,
                sig["kind"] if sig else None,
                crypto.seal(json.dumps(data, ensure_ascii=False), _aad(cid)),
            ),
        )
        audit.append(con, by, "contact.log", cid, {"family_id": family_id, "channel": channel, "signal": signal_id})
    return get(cid)


def _row(r: Any) -> Dict[str, Any]:
    data = json.loads(crypto.open_(r["data"], _aad(r["id"])))
    return {
        "id": r["id"],
        "at": r["at"],
        "family_id": r["family_id"],
        "by": r["by"],
        "from_signal": r["signal"] is not None,
        "channel_label": CHANNELS[data["channel"]],
        **data,
    }


def get(cid: str) -> Dict[str, Any]:
    with db.tx() as con:
        r = con.execute("select * from rm_contacts where id = ?", (cid,)).fetchone()
    if r is None:
        raise BadRequest(f"không có liên hệ {cid}")
    return _row(r)


def recent(families: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """The latest contacts, of ``families`` when given (an RM sees their own families')."""
    with db.tx() as con:
        rows = con.execute("select * from rm_contacts order by at desc").fetchall()
    keep = None if families is None else set(families)
    return [_row(r) for r in rows if keep is None or r["family_id"] in keep][:limit]


def share() -> Dict[str, Any]:
    """Contacts and the share that started from a signal, by month (newest last) and by RM."""
    from measure.reports import _month

    with db.tx() as con:
        rows = [(r["at"], r["by"], r["signal"]) for r in con.execute("select at, by, signal from rm_contacts")]

    def one(xs: List[tuple]) -> Dict[str, Any]:
        n = len(xs)
        k = sum(1 for x in xs if x[2] is not None)
        return {"contacts": n, "from_signal": k, "share": round(k / n, 3) if n else None}

    months = [{"month": m, **one([x for x in rows if _month(x[0]) == m])} for m in sorted({_month(x[0]) for x in rows})]
    people = [{"by": b, **one([x for x in rows if x[1] == b])} for b in sorted({x[1] for x in rows})]
    return {"by_month": months, "by_rm": people, "target": TARGET}

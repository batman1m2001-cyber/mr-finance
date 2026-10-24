"""Alerts (BRD-NFR-12; BRD completion F7): what failed and who should look — a news feed or a market series that
could not be fetched, an agent run that failed, the audit chain broken, a package from the AI zone rejected, the
zone not reached. One open alert per thing (``kind`` + ``key``): failing again counts up on it; the thing working
again resolves it. Staff see their kinds' alerts in the bell and Admin all of them in Hệ thống; acknowledging one
(“Đã xem”) is audited, as are raising and resolving. Every step also goes to the central log (control.log)."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from control import audit, db, log, roles
from control.errors import BadRequest, Conflict

KINDS: Dict[str, Dict[str, Any]] = {
    "news_feed": {"label": "Nguồn tin không lấy được", "roles": ("cio", "admin"), "severity": "medium"},
    "market_job": {"label": "Chuỗi thị trường không lấy được", "roles": ("cio", "admin"), "severity": "medium"},
    "agent": {"label": "Agent lỗi", "roles": ("cio", "admin"), "severity": "high"},
    "audit_chain": {"label": "Chuỗi nhật ký kiểm toán gãy", "roles": ("compliance", "admin"), "severity": "high"},
    "inbox": {"label": "Gói từ vùng AI bị từ chối", "roles": ("cio", "admin"), "severity": "medium"},
    "zone_sync": {"label": "Không gửi được vùng AI", "roles": ("admin",), "severity": "medium"},
    "job": {"label": "Việc nền chạy tay lỗi", "roles": ("admin",), "severity": "medium"},
    "availability": {"label": "Sẵn sàng trong giờ làm việc dưới 99,5 %", "roles": ("admin",), "severity": "high"},
}
ACTOR = "system:alerts"


def _open(con, kind: str, key: str) -> Optional[Dict[str, Any]]:
    q = "select * from alerts where kind = ? and key = ? and status != 'resolved' order by created desc limit 1"
    return db.load(con.execute(q, (kind, key)).fetchone())


def _save(con, a: Dict[str, Any]) -> None:
    data = {k: v for k, v in a.items() if k not in ("id", "kind", "key", "status", "created")}
    con.execute("update alerts set status = ?, data = ? where id = ?", (a["status"], db.dumps(data), a["id"]))


def is_open(kind: str, key: str) -> bool:
    """Whether the thing has an alert not yet resolved (open or acknowledged)."""
    with db.tx() as con:
        return _open(con, kind, key) is not None


def raise_(kind: str, key: str, title: str, detail: str = "") -> Dict[str, Any]:
    """A new alert, or one more occurrence on the open one."""
    k = KINDS[kind]
    now = time.time()
    with db.tx() as con:
        a = _open(con, kind, key)
        if a is not None:
            a.update(count=a["count"] + 1, last_at=now, title=title, detail=str(detail)[:500])
            _save(con, a)
        else:
            aid = f"AL-{db.next_seq(con, 'alert'):06d}"
            a = {
                "id": aid,
                "kind": kind,
                "key": key,
                "status": "open",
                "created": now,
                "title": title[:200],
                "detail": str(detail)[:500],
                "severity": k["severity"],
                "count": 1,
                "last_at": now,
                "history": [],
            }
            con.execute(
                "insert into alerts values (?, ?, ?, ?, ?, ?)",
                (
                    aid,
                    kind,
                    key,
                    "open",
                    now,
                    db.dumps({x: a[x] for x in a if x not in ("id", "kind", "key", "status", "created")}),
                ),
            )
            audit.append(con, ACTOR, "alert.raise", aid, {"kind": kind, "key": key, "title": a["title"]})
    log.write(
        "warning" if k["severity"] == "medium" else "error",
        "alert.raise",
        alert=a["id"],
        kind=kind,
        key=key,
        title=title,
        detail=str(detail)[:500],
        count=a["count"],
    )
    return a


def resolve(kind: str, key: str, note: str = "Hoạt động lại bình thường") -> Optional[Dict[str, Any]]:
    """The thing works again: its open alert, if any, is resolved."""
    with db.tx() as con:
        a = _open(con, kind, key)
        if a is None:
            return None
        a["status"] = "resolved"
        a["history"].append({"at": time.time(), "by": ACTOR, "status": "resolved", "note": note})
        _save(con, a)
        audit.append(con, ACTOR, "alert.resolve", a["id"], {"kind": kind, "key": key})
    log.write("info", "alert.resolve", alert=a["id"], kind=kind, key=key)
    return a


def ack(alert_id: str, by: str, note: str = "") -> Dict[str, Any]:
    """Someone who should look has looked: open → acked (it stays until the thing works again)."""
    roles.require(by, *sorted({r for k in KINDS.values() for r in k["roles"]}))  # before the write: reads people
    with db.tx() as con:
        a = db.load(con.execute("select * from alerts where id = ?", (str(alert_id),)).fetchone())
    if a is None:
        raise BadRequest(f"không có cảnh báo {alert_id}")
    roles.require(by, *KINDS[a["kind"]]["roles"])
    with db.tx() as con:
        a = db.load(con.execute("select * from alerts where id = ?", (str(alert_id),)).fetchone())
        if a["status"] != "open":
            raise Conflict(f"{alert_id} đã {a['status']}")
        a["status"] = "acked"
        a["history"].append({"at": time.time(), "by": by, "status": "acked", "note": str(note or "")[:300]})
        _save(con, a)
        audit.append(con, by, "alert.ack", a["id"], {"kind": a["kind"], "key": a["key"], "note": str(note or "")[:300]})
    log.write("info", "alert.ack", alert=a["id"], kind=a["kind"], key=a["key"], by=by)
    return a


def for_role(role: str, limit: int = 50) -> List[Dict[str, Any]]:
    """What the role should look at: open and acknowledged alerts of its kinds, newest first (Admin: every kind)."""
    kinds = [k for k, v in KINDS.items() if role in v["roles"]]
    if not kinds:
        return []
    marks = ",".join("?" * len(kinds))
    with db.tx() as con:
        rows = con.execute(
            f"select * from alerts where status != 'resolved' and kind in ({marks}) order by created desc limit ?",
            (*kinds, limit),
        ).fetchall()
    return [{**db.load(r), "label": KINDS[r["kind"]]["label"]} for r in rows]


def counts(role: Optional[str] = None) -> Dict[str, int]:
    """How many alerts are not resolved (``total``) and how many nobody has looked at yet (``open``), counted in the
    database: the role's kinds (as ``for_role``), or every kind with no role. ``for_role`` is a page of 50."""
    kinds = [k for k, v in KINDS.items() if role is None or role in v["roles"]]
    if not kinds:
        return {"total": 0, "open": 0}
    marks = ",".join("?" * len(kinds))
    with db.tx() as con:
        rows = con.execute(
            f"select status, count(*) from alerts where status != 'resolved' and kind in ({marks}) group by status",
            kinds,
        ).fetchall()
    by = {r[0]: r[1] for r in rows}
    return {"total": sum(by.values()), "open": by.get("open", 0)}


def recent(limit: int = 30) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from alerts order by created desc limit ?", (limit,)).fetchall()
    return [{**db.load(r), "label": KINDS[r["kind"]]["label"]} for r in rows]

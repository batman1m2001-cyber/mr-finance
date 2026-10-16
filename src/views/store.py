"""Views, challenges, decisions and agent runs, kept (BRD §11.4).

A view is one version of the CIO's reading of an event: ``VW-0007-v1`` for event EV-2026-0007.
Its ``data`` keeps the agent's draft as it came (``draft``), the version the CIO edits and approves
(``current``), every edit, every status change, and the CIO's answers to findings. ``content_hash``
pins what a challenge looked at: approval needs a challenge on the current content.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from control import audit, db

LIFECYCLE = (
    "DRAFTING",
    "PENDING_CHALLENGE",
    "PENDING_APPROVAL",
    "APPROVED",
    "AGENT_ERROR",
    "REWORK_REQUESTED",
    "REJECTED",
    "WITHDRAWN",
    "SUPERSEDED",
)


def content_hash(current: Dict[str, Any]) -> str:
    body = {k: current.get(k) for k in ("summary", "impacts", "scenarios")}
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def _event_seq(event_id: str) -> str:
    return event_id.rsplit("-", 1)[-1]


def create(event_id: str, by: str, mode: str, models: Dict[str, str]) -> Dict[str, Any]:
    now = time.time()
    with db.tx() as con:
        row = con.execute("select max(version) as v from views where event_id = ?", (event_id,)).fetchone()
        version = (row["v"] or 0) + 1
        view_id = f"VW-{_event_seq(event_id)}-v{version}"
        data = {
            "mode": mode,
            "models": models,
            "created_by": by,
            "history": [{"at": now, "by": by, "status": "DRAFTING", "note": ""}],
            "edits": [],
            "responses": {},
        }
        con.execute(
            "insert into views values (?, ?, ?, ?, ?, ?)", (view_id, event_id, version, "DRAFTING", now, db.dumps(data))
        )
        audit.append(con, by, "view.create", view_id, {"event_id": event_id, "mode": mode, "models": models})
    return get(view_id)


def get(view_id: str) -> Dict[str, Any]:
    with db.tx() as con:
        v = db.load(con.execute("select * from views where id = ?", (view_id,)).fetchone())
    if v is None:
        raise KeyError(f"không có nhận định {view_id}")
    return v


def for_event(event_id: str) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from views where event_id = ? order by version", (event_id,)).fetchall()
    return [db.load(r) for r in rows]


def save(view: Dict[str, Any], status: str, by: str, note: str = "") -> Dict[str, Any]:
    """Write the view's data and move it to ``status``, recording who and why."""
    if status not in LIFECYCLE:
        raise ValueError(f"unknown status {status}")
    data = {k: v for k, v in view.items() if k not in ("id", "event_id", "version", "status", "created")}
    if status != view["status"]:
        data["history"] = data.get("history", []) + [{"at": time.time(), "by": by, "status": status, "note": note}]
    with db.tx() as con:
        before = con.execute("select status, data from views where id = ?", (view["id"],)).fetchone()
        con.execute("update views set status = ?, data = ? where id = ?", (status, db.dumps(data), view["id"]))
        old = json.loads(before["data"]) if before else {}
        changed = sorted(k for k in set(old) | set(data) if old.get(k) != data.get(k) and k != "history")
        audit.append(
            con,
            by,
            "view.save",
            view["id"],
            {
                "from": before["status"] if before else None,
                "to": status,
                "note": note,
                "changed": changed,
                "content_hash": data.get("content_hash"),
            },
        )
    return get(view["id"])


def add_challenge(view_id: str, stage: str, data: Dict[str, Any]) -> Dict[str, Any]:
    now = time.time()
    with db.tx() as con:
        n = con.execute("select count(*) from challenges where view_id = ?", (view_id,)).fetchone()[0] + 1
        cid = f"CH-{view_id[3:]}-{n}"
        con.execute("insert into challenges values (?, ?, ?, ?, ?)", (cid, view_id, stage, now, db.dumps(data)))
        audit.append(
            con,
            "agent:challenger",
            "challenge.add",
            cid,
            {
                "view_id": view_id,
                "stage": stage,
                "model": data.get("model"),
                "content_hash": data.get("content_hash"),
                "findings": [[f["id"], f["severity"]] for f in data.get("findings", [])],
            },
        )
    return {**data, "id": cid, "view_id": view_id, "stage": stage, "created": now}


def challenges(view_id: str) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from challenges where view_id = ? order by created", (view_id,)).fetchall()
    return [db.load(r) for r in rows]


def latest_challenge(view_id: str) -> Optional[Dict[str, Any]]:
    got = challenges(view_id)
    return got[-1] if got else None


def add_decision(view_id: str, action: str, idem_key: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
    """A decision; the same ``idem_key`` twice returns the first one (a double click decides once)."""
    now = time.time()
    with db.tx() as con:
        if idem_key:
            old = con.execute("select * from decisions where idem_key = ?", (idem_key,)).fetchone()
            if old is not None:
                return {**db.load(old), "repeated": True}
        seq = db.next_seq(con, "decision")
        did = f"DC-{seq:06d}"
        con.execute(
            "insert into decisions values (?, ?, ?, ?, ?, ?)", (did, view_id, action, idem_key, now, db.dumps(data))
        )
        audit.append(
            con,
            data.get("by", "?"),
            f"decision.{action}",
            did,
            {"view_id": view_id, "reason": data.get("reason"), "content_hash": data.get("content_hash")},
        )
    return {**data, "id": did, "view_id": view_id, "action": action, "idem_key": idem_key, "created": now}


def decisions(view_id: str) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from decisions where view_id = ? order by created", (view_id,)).fetchall()
    return [db.load(r) for r in rows]


def find_decision(idem_key: str) -> Optional[Dict[str, Any]]:
    with db.tx() as con:
        return db.load(con.execute("select * from decisions where idem_key = ?", (idem_key,)).fetchone())


# -- agent runs: every node's input, prompt, model, output and time (FR-704) --------------------


def start_run(agent: str, subject_id: str, mode: str, model: str) -> str:
    now = time.time()
    with db.tx() as con:
        seq = db.next_seq(con, "agent_run")
        rid = f"AG-{seq:06d}"
        data = {"mode": mode, "model": model, "nodes": [], "status": "running"}
        con.execute("insert into agent_runs values (?, ?, ?, ?, ?)", (rid, agent, subject_id, now, db.dumps(data)))
        audit.append(con, f"agent:{agent}", "agent.start", rid, {"subject": subject_id, "mode": mode, "model": model})
    return rid


def add_node(run_id: str, node: Dict[str, Any]) -> None:
    with db.tx() as con:
        row = con.execute("select data from agent_runs where id = ?", (run_id,)).fetchone()
        data = json.loads(row["data"])
        data["nodes"].append({**node, "seq": len(data["nodes"]) + 1})
        con.execute("update agent_runs set data = ? where id = ?", (db.dumps(data), run_id))


def finish_run(run_id: str, status: str, error: str = "") -> None:
    with db.tx() as con:
        row = con.execute("select data from agent_runs where id = ?", (run_id,)).fetchone()
        data = json.loads(row["data"])
        data.update(status=status, error=error, finished=time.time())
        con.execute("update agent_runs set data = ? where id = ?", (db.dumps(data), run_id))
        nodes = hashlib.sha256(db.dumps(data["nodes"]).encode("utf-8")).hexdigest()
        who = con.execute("select agent, subject_id from agent_runs where id = ?", (run_id,)).fetchone()
        audit.append(
            con,
            "agent",
            "agent.finish",
            run_id,
            {"status": status, "error": error, "nodes": len(data["nodes"]), "nodes_hash": nodes},
        )
    from control import alerts  # after the write: an alert is its own transaction (NFR-12)

    if status == "error":
        alerts.raise_("agent", who["agent"], f"Agent {who['agent']} lỗi ({who['subject_id']}, {run_id})", error)
    elif status == "ok":
        alerts.resolve("agent", who["agent"])


def runs(subject_id: str) -> List[Dict[str, Any]]:
    with db.tx() as con:
        rows = con.execute("select * from agent_runs where subject_id = ? order by created", (subject_id,)).fetchall()
    return [db.load(r) for r in rows]


def run_health(days: int = 7) -> List[Dict[str, Any]]:
    """Per agent over the last ``days``: runs, failures, the last run's time, status and error (Hệ thống)."""
    since = time.time() - days * 86400
    with db.tx() as con:
        rows = con.execute(
            "select agent, created, json_extract(data, '$.status') as status, json_extract(data, '$.error') as error "
            "from agent_runs where created >= ? order by created",
            (since,),
        ).fetchall()
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        a = out.setdefault(r["agent"], {"agent": r["agent"], "runs": 0, "failed": 0})
        a["runs"] += 1
        a["failed"] += r["status"] == "error"
        a.update(last=r["created"], last_status=r["status"], last_error=r["error"] or None)
    return sorted(out.values(), key=lambda a: a["agent"])


def tokens(since: float = 0.0) -> Dict[str, Any]:
    """NFR-10: tokens the agents used since ``since``, in total and per subject (an event): the cost per event."""
    total, by = 0, {}
    with db.tx() as con:
        rows = con.execute("select subject_id, data from agent_runs where created >= ?", (since,)).fetchall()
    for r in rows:
        n = sum((x.get("tokens_in") or 0) + (x.get("tokens_out") or 0) for x in json.loads(r["data"])["nodes"])
        total += n
        by[r["subject_id"]] = by.get(r["subject_id"], 0) + n
    return {"total": total, "by_subject": by}

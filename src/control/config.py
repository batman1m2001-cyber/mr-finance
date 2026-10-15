"""Versioned, owned configuration (BRD FR-701, §13.1, ADR-0016): propose, then approve.

Kinds: the factor model, alert thresholds, the restricted list, the news sources (white list). Version 1 of each
is the file shipped in data/ (or the defaults below); every change is a new version that is PROPOSED, then
APPROVED (it becomes ACTIVE and the one before SUPERSEDED) or REJECTED, by a user of the owner's role. Where
§13.1 and F14 ask for two people, the approver must not be the proposer. Every step is in the audit chain, and
the content of each version is hashed.
"""

from __future__ import annotations

import hashlib
import json
import time
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

from control import audit, db, roles
from wealth.paths import DATA

THRESHOLDS = {  # BR-09 and the FR-501 post-check rules
    "pre_review_pct": -0.05,
    "concentration_share": 0.4,
    "modelled_share": 0.5,
    "implausible_share": 0.25,
}


@lru_cache(maxsize=8)
def _load(name: str) -> str:
    return (DATA / name).read_text(encoding="utf-8")


def _file(name: str, key: Optional[str] = None) -> Callable[[], Any]:
    def read() -> Any:  # a fresh copy each time: callers may change what they get
        data = json.loads(_load(name))
        return data[key] if key else data

    return read


def _check_model(data: Any) -> None:
    from engine import FactorModel

    FactorModel.from_dict(data)


def _check_thresholds(data: Any) -> None:
    if set(data) != set(THRESHOLDS):
        raise ValueError(f"ngưỡng phải có đúng các khóa {sorted(THRESHOLDS)}")
    if not all(isinstance(v, (int, float)) for v in data.values()):
        raise ValueError("ngưỡng phải là số")
    if not -0.5 <= data["pre_review_pct"] < 0:
        raise ValueError("pre_review_pct trong khoảng −0,5 … 0")
    for k in ("concentration_share", "modelled_share", "implausible_share"):
        if not 0 < data[k] <= 1:
            raise ValueError(f"{k} trong khoảng 0 … 1")


def _check_restricted(data: Any) -> None:
    if not isinstance(data, list) or not data:
        raise ValueError("danh sách hạn chế là một danh sách khác rỗng")
    for r in data:
        if not (isinstance(r, dict) and r.get("name") and r.get("ticker") and isinstance(r.get("aliases"), list)):
            raise ValueError("mỗi mục cần name, ticker, aliases")


def _check_sources(data: Any) -> None:
    if not isinstance(data, list) or not data:
        raise ValueError("danh sách nguồn là một danh sách khác rỗng")
    ids = set()
    for s in data:
        if not (isinstance(s, dict) and s.get("id") and str(s.get("url", "")).startswith("https://")):
            raise ValueError("mỗi nguồn cần id và url https")
        if s.get("kind") not in ("domestic", "intl"):
            raise ValueError(f"{s['id']}: kind là domestic hoặc intl")
        if s["id"] in ids:
            raise ValueError(f"nguồn {s['id']} bị trùng")
        ids.add(s["id"])


KINDS: Dict[str, Dict[str, Any]] = {
    "factor_model": {
        "label": "Mô hình yếu tố",
        "owner": "cio",
        "two_person": True,
        "base": _file("factor_model.json"),
        "check": _check_model,
    },
    "thresholds": {
        "label": "Ngưỡng cảnh báo",
        "owner": "cio",
        "two_person": True,
        "base": lambda: dict(THRESHOLDS),
        "check": _check_thresholds,
    },
    "restricted": {
        "label": "Danh sách hạn chế",
        "owner": "compliance",
        "two_person": True,
        "base": _file("news_config.json", "restricted"),
        "check": _check_restricted,
    },
    "news_sources": {
        "label": "Nguồn tin (danh sách trắng)",
        "owner": "admin",
        "two_person": False,
        "base": _file("news_config.json", "sources"),
        "check": _check_sources,
    },
}


def _hash(data: Any) -> str:
    return hashlib.sha256(db.dumps(data).encode("utf-8")).hexdigest()


def _kind(kind: str) -> Dict[str, Any]:
    if kind not in KINDS:
        raise ValueError(f"không có loại cấu hình {kind!r}")
    return KINDS[kind]


@lru_cache(maxsize=None)
def _base_text(kind: str) -> tuple:
    """The shipped version as canonical JSON and its hash (files do not change while the app runs)."""
    data = _kind(kind)["base"]()
    return db.dumps(data), _hash(data)


def _base(kind: str) -> Dict[str, Any]:
    text, h = _base_text(kind)
    return {
        "id": f"CF-{kind}-v1",
        "kind": kind,
        "version": 1,
        "status": "ACTIVE",
        "created": 0.0,
        "data": json.loads(text),
        "hash": h,
        "proposed_by": "tệp gốc",
        "note": "Bản phát hành cùng mã nguồn",
        "history": [],
    }


_CACHE: Dict[tuple, tuple] = {}  # (kind, state file) → (canonical JSON, hash) of the version in force


def clear_cache() -> None:
    """Called on every write here and on the demo reset: the next read goes to the database again."""
    _CACHE.clear()


def _in_force(kind: str) -> tuple:
    _kind(kind)
    from wealth.paths import state_path

    path = state_path()
    if not path.exists():  # no state yet, so no versions: the shipped file, without creating the database
        return _base_text(kind)
    key = (kind, str(path))
    if key not in _CACHE:
        with db.tx() as con:
            q = "select data from config_versions where kind = ? and status = 'ACTIVE'"
            row = con.execute(q, (kind,)).fetchone()
        if row:
            d = json.loads(row["data"])
            _CACHE[key] = (db.dumps(d["data"]), d["hash"])
        else:
            _CACHE[key] = _base_text(kind)
    return _CACHE[key]


def active_hash(kind: str) -> str:
    """The hash of the version in force, without loading it (for caches keyed by version)."""
    return _in_force(kind)[1]


def versions(kind: str) -> List[Dict[str, Any]]:
    """Every version, newest first; version 1 is the shipped file (ACTIVE until another is approved)."""
    _kind(kind)
    with db.tx() as con:
        q = "select * from config_versions where kind = ? order by version desc"
        rows = [db.load(r) for r in con.execute(q, (kind,))]
    base = _base(kind)
    if any(r["status"] == "ACTIVE" for r in rows):
        base["status"] = "SUPERSEDED"
    return rows + [base]


def active(kind: str) -> Dict[str, Any]:
    return next(v for v in versions(kind) if v["status"] == "ACTIVE")


def data(kind: str) -> Any:
    """What the product uses now for ``kind`` (a fresh copy)."""
    return json.loads(_in_force(kind)[0])


def propose(kind: str, new: Any, by: str, note: str = "") -> Dict[str, Any]:
    k = _kind(kind)
    roles.require(by, k["owner"])
    k["check"](new)
    if _hash(new) == active(kind)["hash"]:
        raise ValueError("Nội dung giống bản đang áp dụng")
    now = time.time()
    with db.tx() as con:
        if con.execute("select 1 from config_versions where kind = ? and status = 'PROPOSED'", (kind,)).fetchone():
            raise ValueError("Đã có một đề xuất đang chờ cho loại cấu hình này")
        row = con.execute("select max(version) as v from config_versions where kind = ?", (kind,)).fetchone()
        version = max(1, row["v"] or 1) + 1
        vid = f"CF-{kind}-v{version}"
        body = {
            "data": new,
            "hash": _hash(new),
            "proposed_by": by,
            "note": str(note or "")[:500],
            "history": [{"at": now, "by": by, "status": "PROPOSED", "note": str(note or "")[:500]}],
        }
        con.execute(
            "insert into config_versions values (?, ?, ?, ?, ?, ?)",
            (vid, kind, version, "PROPOSED", now, db.dumps(body)),
        )
        audit.append(con, by, "config.propose", vid, {"kind": kind, "hash": body["hash"]})
    clear_cache()
    return next(v for v in versions(kind) if v["id"] == vid)


def decide(version_id: str, action: str, by: str, note: str = "") -> Dict[str, Any]:
    if action not in ("approve", "reject"):
        raise ValueError("action là approve hoặc reject")
    with db.tx() as con:
        v = db.load(con.execute("select * from config_versions where id = ?", (version_id,)).fetchone())
        if v is None:
            raise ValueError(f"không có phiên bản {version_id}")
        k = _kind(v["kind"])
        roles.require(by, k["owner"])
        if v["status"] != "PROPOSED":
            raise ValueError(f"{version_id} đã {v['status']}")
        if action == "approve" and k["two_person"] and by == v["proposed_by"]:
            raise roles.Forbidden("Cần người thứ hai duyệt: người đề xuất không tự duyệt (§13.1)")
        now = time.time()
        status = "ACTIVE" if action == "approve" else "REJECTED"
        if status == "ACTIVE":
            q = "select id, data from config_versions where kind = ? and status = 'ACTIVE'"
            for old in con.execute(q, (v["kind"],)).fetchall():
                d = json.loads(old["data"])
                d["history"].append({"at": now, "by": by, "status": "SUPERSEDED", "note": version_id})
                q2 = "update config_versions set status = 'SUPERSEDED', data = ? where id = ?"
                con.execute(q2, (db.dumps(d), old["id"]))
        body = {k2: v[k2] for k2 in ("data", "hash", "proposed_by", "note", "history")}
        body["history"].append({"at": now, "by": by, "status": status, "note": str(note or "")[:500]})
        body["decided_by"] = by
        q = "update config_versions set status = ?, data = ? where id = ?"
        con.execute(q, (status, db.dumps(body), version_id))
        audit.append(con, by, f"config.{action}", version_id, {"kind": v["kind"], "hash": v["hash"]})
    clear_cache()
    return next(x for x in versions(v["kind"]) if x["id"] == version_id)


def overview() -> List[Dict[str, Any]]:
    out = []
    for kind, k in KINDS.items():
        vs = versions(kind)
        keep = ("id", "version", "status", "created", "proposed_by", "decided_by", "note", "hash")
        out.append(
            {
                "kind": kind,
                "label": k["label"],
                "owner": k["owner"],
                "owner_label": roles.ROLE_LABELS[k["owner"]],
                "two_person": k["two_person"],
                "active": next(v for v in vs if v["status"] == "ACTIVE"),
                "pending": next((v for v in vs if v["status"] == "PROPOSED"), None),
                "versions": [{x: v.get(x) for x in keep} for v in vs],
            }
        )
    return out

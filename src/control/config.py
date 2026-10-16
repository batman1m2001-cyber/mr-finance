"""Versioned, owned configuration (BRD FR-701, §13.1, ADR-0016): propose, then approve.

Kinds (BRD-RULE-SEC-05): the factor model, alert thresholds and return assumptions (CIO); the restricted list,
forbidden phrases and data-sharing consent (Compliance); the news sources, the market data sources and the ticker
map (Admin); the agents' prompts and models (Admin). Version 1 of each is the file shipped in data/ (or the
defaults in code; for the models, what the deployment set in .env); every change is a new version that is
PROPOSED, then APPROVED (it becomes ACTIVE and the one before SUPERSEDED) or REJECTED, by a user of the owner's
role. Where §13.1 and F14 ask for two people, the approver must not be the proposer. A prompt or model proposal
is approved only after the fixed eval set passed on it (MEAS-07, ``views.evalset``, the ``agent_eval`` job). Every
step is in the audit chain, and the content of each version is hashed.
"""

from __future__ import annotations

import hashlib
import json
import re
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


def _check_price_sources(data: Any) -> None:
    from market.sources import ADAPTERS

    if not isinstance(data, dict) or not isinstance(data.get("series"), list) or not data["series"]:
        raise ValueError("nguồn giá cần danh sách series khác rỗng")
    jobs = data.get("jobs") or {}
    ids = set()
    for s in data["series"]:
        if not (isinstance(s, dict) and s.get("id") and s.get("job") in jobs and s.get("sources")):
            raise ValueError("mỗi series cần id, job (trong jobs) và sources")
        if s["id"] in ids:
            raise ValueError(f"series {s['id']} bị trùng")
        ids.add(s["id"])
        for src in s["sources"]:
            if src.get("source") not in ADAPTERS or not src.get("symbol"):
                raise ValueError(f"{s['id']}: nguồn {src.get('source')!r} không có (có: {sorted(ADAPTERS)})")


RETURNS = {  # the life-scenario simulator's rates a year (scenarios._sim)
    "safe": 0.05,  # a 12-month deposit
    "growth": 0.07,  # a balanced portfolio, long run
    "inflation": 0.04,
    "withdrawal": 0.04,  # what a pot can pay out a year without running down
    "rental_yield": 0.035,  # gross rent of a property a year
    "best_deposit": 0.065,  # the best 12-month deposit on the market (what idle cash is compared to)
}


def _check_returns(data: Any) -> None:
    if not isinstance(data, dict) or set(data) != set(RETURNS):
        raise ValueError(f"giả định lợi suất phải có đúng các khóa {sorted(RETURNS)}")
    for k, v in data.items():
        if not isinstance(v, (int, float)) or not 0 <= v <= 0.3:
            raise ValueError(f"{k}: một tỷ lệ năm trong khoảng 0 … 0,3")
    if data["safe"] > data["best_deposit"]:
        raise ValueError("safe không lớn hơn best_deposit (lãi tiền gửi tốt nhất)")


def _forbidden_base() -> Dict[str, List[str]]:
    from procedural import goals
    from views import schema

    return {"recommendation": list(schema.FORBIDDEN), "compliance": list(goals.FORBIDDEN)}


def _check_forbidden(data: Any) -> None:
    if not isinstance(data, dict) or set(data) != {"recommendation", "compliance"}:
        raise ValueError("cần hai danh sách: recommendation (khuyến nghị mua/bán) và compliance (ghi chú quy định)")
    for k, words in data.items():
        if not isinstance(words, list) or not words:
            raise ValueError(f"{k}: một danh sách khác rỗng")
        if not all(isinstance(w, str) and w.strip() and len(w) <= 60 for w in words):
            raise ValueError(f"{k}: mỗi cụm từ là chuỗi 1–60 ký tự")


CONSENT = {
    "version": "2026-10",
    "text": (
        "Tôi đồng ý cho Ngân hàng đọc số dư và giao dịch của tôi tại các tổ chức tôi chọn (qua Open API theo khuôn khổ "
        "của NHNN) và cho thành viên chủ hộ xem tài sản của tôi trong bức tranh gia đình. Tôi có thể rút lại đồng ý "
        "bất cứ lúc nào."
    ),
    "require": {"open_api": True, "family_member": True},
}


def _check_consent(data: Any) -> None:
    if not isinstance(data, dict) or not str(data.get("version", "")).strip():
        raise ValueError("cần version của mẫu đồng ý")
    if not isinstance(data.get("text"), str) or len(data["text"].strip()) < 40:
        raise ValueError("cần nội dung đồng ý (ít nhất 40 ký tự)")
    req = data.get("require")
    if (
        not isinstance(req, dict)
        or set(req) != set(CONSENT["require"])
        or not all(isinstance(v, bool) for v in req.values())
    ):
        raise ValueError(f"require: đúng các khóa {sorted(CONSENT['require'])}, giá trị true/false")


AI_MODES = ("live", "inbox", "mock")


def _check_ai_mode(data: Any) -> None:
    if not isinstance(data, dict) or set(data) != {"mode"} or data["mode"] not in AI_MODES:
        raise ValueError(f"cần {{'mode': một trong {list(AI_MODES)}}}")


def _client_ai_base() -> Dict[str, Any]:
    from control.barrier import BASE

    return json.loads(json.dumps(BASE))


def _check_client_ai(data: Any) -> None:
    from control.barrier import MODES

    if not isinstance(data, dict) or set(data) != {"mode", "onprem_hosts"} or data["mode"] not in MODES:
        raise ValueError(f"cần {{'mode': một trong {list(MODES)}, 'onprem_hosts': [máy chủ]}}")
    hosts = data["onprem_hosts"]
    if not isinstance(hosts, list) or len(hosts) > 20:
        raise ValueError("onprem_hosts: danh sách tối đa 20 tên máy chủ")
    if not all(isinstance(h, str) and re.fullmatch(r"[A-Za-z0-9.-]{1,253}", h) for h in hosts):
        raise ValueError("onprem_hosts: mỗi mục là một tên máy chủ hoặc địa chỉ IP, không có giao thức hay cổng")
    if data["mode"] == "onprem" and not hosts:
        raise ValueError("chế độ onprem cần ít nhất một máy chủ trong onprem_hosts")


def _check_assistant_retention(data: Any) -> None:
    if not isinstance(data, dict) or set(data) != {"archive_days"}:
        raise ValueError("cần {'archive_days': số ngày}")
    n = data["archive_days"]
    if not isinstance(n, int) or isinstance(n, bool) or not 30 <= n <= 3650:
        raise ValueError("archive_days: số ngày nguyên từ 30 đến 3.650")


def _check_related(data: Any) -> None:
    if not isinstance(data, list) or not 1 <= len(data) <= 100:
        raise ValueError("một danh sách 1–100 tên bên liên quan")
    if not all(isinstance(p, str) and 2 <= len(p.strip()) <= 80 for p in data):
        raise ValueError("mỗi tên là chuỗi 2–80 ký tự")


# the bank and its group (BRD §14 CONTENT-03 names “tổ chức liên quan tới TCB hoặc TCBS”); Compliance keeps the list
RELATED = ["Techcombank", "TCB", "TCBS", "Techcom Securities", "Techcom Capital", "Techcom Life"]


def _assignment_base() -> Dict[str, str]:
    from people import store

    return {fam: t["rm"] for fam, t in sorted(store._seed_staff()["teams"].items())}


def _check_assignment(data: Any) -> None:
    from people import store

    if not isinstance(data, dict):
        raise ValueError("cần {mã gia đình: mã RM}")
    families = set(store.client_ids())
    missing, extra = sorted(families - set(data)), sorted(set(data) - families)
    if missing or extra:
        raise ValueError(f"mỗi gia đình đúng một RM; thiếu {missing}, không có {extra}")
    rms = {p["id"] for p in store.staff("rm")}
    bad = sorted(f"{f}: {r}" for f, r in data.items() if r not in rms)
    if bad:
        raise ValueError(f"không phải RM: {bad}")


# Who may approve action recommendations (BRD-RULE-ROLE-05, WF-08; BRD_REMAINING_PLAN G8, G-D7): a specialist with a
# certificate in force. Demo values, not real certificates; two specialists are left uncertified on purpose.
CERTIFICATIONS = {
    "sp_global": {"certificate": "CFA (demo)", "issuer": "CFA Institute", "valid_until": "2027-12-31"},
    "sp_insurance": {
        "certificate": "Tư vấn bảo hiểm nhân thọ (demo)",
        "issuer": "Bộ Tài chính",
        "valid_until": "2027-06-30",
    },
    "sp_private": {"certificate": "CFP (demo)", "issuer": "FPSB", "valid_until": "2028-03-31"},
}


def _check_certifications(data: Any) -> None:
    from datetime import date

    from people import store

    if not isinstance(data, dict):
        raise ValueError("cần {mã chuyên gia: {certificate, issuer, valid_until}}")
    specialists = {p["id"] for p in store.staff("specialist")}
    for sid, c in data.items():
        if sid not in specialists:
            raise ValueError(f"{sid!r} không phải chuyên gia")
        if not isinstance(c, dict) or not str(c.get("certificate") or "").strip() or len(str(c["certificate"])) > 100:
            raise ValueError(f"{sid}: cần tên chứng chỉ (tối đa 100 ký tự)")
        if not str(c.get("issuer") or "").strip():
            raise ValueError(f"{sid}: cần nơi cấp")
        try:
            date.fromisoformat(str(c.get("valid_until")))
        except ValueError:
            raise ValueError(f"{sid}: valid_until là ngày YYYY-MM-DD") from None


# The control group (BRD-RULE-MEAS-06; BRD_REMAINING_PLAN G9, G-D8): a share of the families, stratified, drawn
# from a seed so anyone can draw it again (measure/control.py).
CONTROL_GROUP = {"share": 0.1, "seed": "MEAS-06-2026", "strata": ["segment", "rm"]}


def _check_control_group(data: Any) -> None:
    if not isinstance(data, dict) or set(data) != {"share", "seed", "strata"}:
        raise ValueError("cần {share, seed, strata}")
    share = data["share"]
    if not isinstance(share, (int, float)) or isinstance(share, bool) or not 0 <= share <= 0.5:
        raise ValueError("share là tỷ lệ từ 0 đến 0,5")
    if not isinstance(data["seed"], str) or not data["seed"].strip():
        raise ValueError("cần seed (chuỗi) để rút lại được nhóm")
    if not isinstance(data["strata"], list) or not set(data["strata"]) <= {"segment", "rm"}:
        raise ValueError("strata là các mục trong segment, rm")


def _models_base() -> Dict[str, str]:
    import os

    return {
        "cio": (os.environ.get("LLM_MODEL_CIO") or "").strip(),
        "challenger": (os.environ.get("LLM_MODEL_CHALLENGER") or "").strip(),
    }


def _check_models(data: Any) -> None:
    if not isinstance(data, dict) or set(data) != {"cio", "challenger"}:
        raise ValueError("cần đúng hai mô hình: cio và challenger")
    if not all(isinstance(v, str) and v.strip() and len(v) <= 120 for v in data.values()):
        raise ValueError("tên mô hình là chuỗi 1–120 ký tự")
    if data["cio"].strip() == data["challenger"].strip():
        raise ValueError("Agent CIO và Agent Phản biện phải dùng hai mô hình khác nhau (§8.3)")


def _prompts_base() -> Dict[str, Any]:
    from views import prompts

    return prompts.default()


def _check_prompts(data: Any) -> None:
    from views import prompts

    prompts.check(data)


def _check_ticker_map(data: Any) -> None:
    if not isinstance(data, dict) or not data:
        raise ValueError("bảng mã là một bảng khác rỗng")
    for k, v in data.items():
        if not (isinstance(k, str) and isinstance(v, str) and v.isalnum()):
            raise ValueError(f"mã {k!r} → {v!r} không hợp lệ")


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
    "return_assumptions": {
        "label": "Giả định lợi suất",
        "owner": "cio",
        "two_person": False,
        "base": lambda: dict(RETURNS),
        "check": _check_returns,
    },
    "restricted": {
        "label": "Danh sách hạn chế",
        "owner": "compliance",
        "two_person": True,
        "base": _file("news_config.json", "restricted"),
        "check": _check_restricted,
    },
    "forbidden_phrases": {
        "label": "Cụm từ cấm",
        "owner": "compliance",
        "two_person": False,
        "base": _forbidden_base,
        "check": _check_forbidden,
    },
    "consent": {
        "label": "Đồng ý chia sẻ dữ liệu",
        "owner": "compliance",
        "two_person": False,
        "base": lambda: json.loads(json.dumps(CONSENT)),
        "check": _check_consent,
    },
    "related_parties": {
        "label": "Bên liên quan (xung đột lợi ích)",
        "owner": "compliance",
        "two_person": False,
        "base": lambda: list(RELATED),
        "check": _check_related,
    },
    "news_sources": {
        "label": "Nguồn tin (danh sách trắng)",
        "owner": "admin",
        "two_person": False,
        "base": _file("news_config.json", "sources"),
        "check": _check_sources,
    },
    "price_sources": {
        "label": "Nguồn dữ liệu thị trường",
        "owner": "admin",
        "two_person": False,
        "base": lambda: {k: v for k, v in _file("market_sources.json")().items() if k != "ticker_map"},
        "check": _check_price_sources,
    },
    "ticker_map": {
        "label": "Bảng mã chứng khoán",
        "owner": "admin",
        "two_person": False,
        "base": _file("market_sources.json", "ticker_map"),
        "check": _check_ticker_map,
    },
    "rm_assignment": {
        "label": "Phân công RM",
        "owner": "admin",
        "two_person": False,
        "base": _assignment_base,
        "check": _check_assignment,
    },
    "certifications": {
        "label": "Chứng nhận chuyên gia",
        "owner": "compliance",
        "two_person": True,
        "base": lambda: json.loads(json.dumps(CERTIFICATIONS)),
        "check": _check_certifications,
    },
    "control_group": {
        "label": "Nhóm đối chứng",
        "owner": "compliance",
        "two_person": True,
        "base": lambda: json.loads(json.dumps(CONTROL_GROUP)),
        "check": _check_control_group,
    },
    "assistant_retention": {
        "label": "Lưu giữ hội thoại với trợ lý",
        "owner": "compliance",
        "two_person": True,
        "base": lambda: {"archive_days": 365},  # a conversation is deleted this long after its last turn (A4)
        "check": _check_assistant_retention,
    },
    "ai_mode": {
        "label": "Chế độ chạy AI",
        "owner": "admin",
        "two_person": False,
        "base": lambda: {"mode": "live"},
        "check": _check_ai_mode,
    },
    "client_ai": {
        "label": "AI với dữ liệu khách hàng",
        "owner": "admin",
        "two_person": True,
        "base": _client_ai_base,
        "check": _check_client_ai,
    },
    "prompts": {
        "label": "Lời nhắc của agent",
        "owner": "admin",
        "two_person": True,
        "eval": True,
        "base": _prompts_base,
        "check": _check_prompts,
    },
    "models": {
        "label": "Mô hình AI của agent",
        "owner": "admin",
        "two_person": True,
        "eval": True,
        "from_env": True,  # version 1 is what the deployment set (LLM_MODEL_CIO, LLM_MODEL_CHALLENGER)
        "base": _models_base,
        "check": _check_models,
    },
}


def _hash(data: Any) -> str:
    return hashlib.sha256(db.dumps(data).encode("utf-8")).hexdigest()


def _kind(kind: str) -> Dict[str, Any]:
    if kind not in KINDS:
        raise ValueError(f"không có loại cấu hình {kind!r}")
    return KINDS[kind]


def _base_text(kind: str) -> tuple:
    """The shipped version as canonical JSON and its hash (files do not change while the app runs; the models'
    version 1 is read from the environment each time)."""
    if _kind(kind).get("from_env"):
        data = KINDS[kind]["base"]()
        return db.dumps(data), _hash(data)
    return _base_file_text(kind)


@lru_cache(maxsize=None)
def _base_file_text(kind: str) -> tuple:
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
        elif KINDS[kind].get("from_env"):
            return _base_text(kind)
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
        if action == "approve" and k.get("eval"):
            ev = v.get("eval") or {}
            if ev.get("status") != "done":
                raise ValueError("Chưa duyệt được: bộ đánh giá cố định chưa chạy xong trên đề xuất này (MEAS-07)")
            if not ev.get("passed"):
                raise ValueError(f"Chưa duyệt được: đề xuất không qua bộ đánh giá cố định — {ev.get('summary', '')}")
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
        if v.get("eval"):
            body["eval"] = v["eval"]
        body["history"].append({"at": now, "by": by, "status": status, "note": str(note or "")[:500]})
        body["decided_by"] = by
        q = "update config_versions set status = ?, data = ? where id = ?"
        con.execute(q, (status, db.dumps(body), version_id))
        audit.append(con, by, f"config.{action}", version_id, {"kind": v["kind"], "hash": v["hash"]})
    clear_cache()
    return next(x for x in versions(v["kind"]) if x["id"] == version_id)


def mirror(kind: str, new: Any, source_id: str, by: str = "tcb:sync") -> Optional[Dict[str, Any]]:
    """The AI zone only (F-D7, ZONE-06): a version TCB approved, put in force here as it is, with TCB's id. None when
    it is the one already in force. Elsewhere a version comes in force only through propose and decide."""
    from wealth.paths import in_zone

    if not in_zone():
        raise roles.Forbidden("Chỉ vùng AI nhận cấu hình đã duyệt từ TCB")
    k = _kind(kind)
    k["check"](new)
    h = _hash(new)
    if h == active(kind)["hash"]:
        return None
    now = time.time()
    with db.tx() as con:
        row = con.execute("select max(version) as v from config_versions where kind = ?", (kind,)).fetchone()
        version = max(1, row["v"] or 1) + 1
        vid = f"CF-{kind}-v{version}"
        for old in con.execute("select id, data from config_versions where kind = ? and status = 'ACTIVE'", (kind,)):
            d = json.loads(old["data"])
            d["history"].append({"at": now, "by": by, "status": "SUPERSEDED", "note": vid})
            con.execute(
                "update config_versions set status = 'SUPERSEDED', data = ? where id = ?", (db.dumps(d), old["id"])
            )
        note = f"Bản {source_id} đã duyệt ở TCB"
        body = {
            "data": new,
            "hash": h,
            "proposed_by": by,
            "decided_by": by,
            "note": note,
            "mirrored_from": source_id,
            "history": [{"at": now, "by": by, "status": "ACTIVE", "note": note}],
        }
        con.execute(
            "insert into config_versions values (?, ?, ?, ?, ?, ?)", (vid, kind, version, "ACTIVE", now, db.dumps(body))
        )
        audit.append(con, by, "config.mirror", vid, {"kind": kind, "hash": h, "from": source_id})
    clear_cache()
    return next(v for v in versions(kind) if v["id"] == vid)


def get(version_id: str) -> Dict[str, Any]:
    with db.tx() as con:
        v = db.load(con.execute("select * from config_versions where id = ?", (version_id,)).fetchone())
    if v is None:
        raise ValueError(f"không có phiên bản {version_id}")
    return v


def pending_evals() -> List[Dict[str, Any]]:
    """Proposals of an eval-gated kind whose eval has not finished (or started more than 30 minutes ago)."""
    out = []
    for kind, k in KINDS.items():
        if not k.get("eval"):
            continue
        for v in versions(kind):
            ev = v.get("eval") or {}
            if v["status"] == "PROPOSED" and (
                not ev or (ev.get("status") == "running" and time.time() - ev.get("started", 0) > 1800)
            ):
                out.append(v)
    return out


def set_eval(version_id: str, result: Dict[str, Any]) -> None:
    """The eval set's state or result on a proposal (MEAS-07); in the audit chain when it is done."""
    with db.tx() as con:
        row = con.execute("select data, status from config_versions where id = ?", (version_id,)).fetchone()
        if row is None or row["status"] != "PROPOSED":
            return
        d = json.loads(row["data"])
        d["eval"] = result
        con.execute("update config_versions set data = ? where id = ?", (db.dumps(d), version_id))
        if result.get("status") == "done":
            audit.append(
                con,
                "job:agent_eval",
                "config.eval",
                version_id,
                {"passed": result.get("passed"), "summary": result.get("summary"), "runs": result.get("runs")},
            )


def overview() -> List[Dict[str, Any]]:
    out = []
    for kind, k in KINDS.items():
        vs = versions(kind)
        keep = ("id", "version", "status", "created", "proposed_by", "decided_by", "note", "hash", "eval")
        out.append(
            {
                "kind": kind,
                "label": k["label"],
                "owner": k["owner"],
                "owner_label": roles.ROLE_LABELS[k["owner"]],
                "two_person": k["two_person"],
                "eval": bool(k.get("eval")),
                "active": next(v for v in vs if v["status"] == "ACTIVE"),
                "pending": next((v for v in vs if v["status"] == "PROPOSED"), None),
                "versions": [{x: v.get(x) for x in keep} for v in vs],
            }
        )
    return out

"""Admin's users and roles (Q-25; owner 2026-10-18, docs/OWNER_BACKLOG_1018_PLAN.md U): staff accounts are added,
moved to another role, disabled, enabled and given a new password, each as a request one Admin makes and another
Admin approves (the configuration's two-person rule, BRD-FR-701), every step audited.

- **Requests** (``account_requests``): ``add`` (name, email as the login, role, title), ``role``, ``disable``,
  ``enable``, ``reset``. One open request per person (an ``add`` per email). The proposer may withdraw it; another
  Admin approves or rejects it (a rejection says why). The checks run again when it is approved: the state may
  have moved since.
- **At once.** A disabled account fails sign-in, and its open sessions fail ``people.auth.verify`` on their next
  request; a role is read from the people table at every request.
- **No password travels.** An approved ``add`` or ``reset`` makes a one-time code (:data:`CODE_TTL`), shown once in
  the approval's answer, for the approving Admin to hand over; only its hash is kept. The person sets their password
  with it (:func:`redeem`, the sign-in page's “Có mã một lần?”). A reset also voids the old password.
- **Guards.** Nobody files a request on their own account; the last enabled Admin is never disabled or moved; an RM
  who still has families in the RM assignment is never disabled or moved (move them first: Cấu hình › Phân công RM,
  two people); while ``MF_DEMO_ACCOUNTS`` is on, the demo's seeded accounts are protected, so a visitor cannot lock
  the next one out. Customers' accounts are not managed here.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import time
from typing import Any, Dict, List, Optional

from control import audit, roles
from control import db as control_db
from control.errors import Conflict
from people import auth, store

KINDS = {
    "add": "Thêm tài khoản",
    "role": "Đổi vai trò",
    "disable": "Khoá tài khoản",
    "enable": "Mở lại tài khoản",
    "reset": "Đặt lại mật khẩu",
}
ACTIONS = ("approve", "reject", "withdraw")
STATUS = {"pending": "Chờ Quản trị thứ hai", "approved": "Đã duyệt", "rejected": "Bị từ chối", "withdrawn": "Đã rút"}
CODE_TTL = 24 * 3600
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I: read aloud or copied by hand
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AccountError(ValueError):
    """A request the guards refuse, with why (answered 400)."""


# -- the flags and the requests -------------------------------------------------------------------


def _row(r) -> Dict[str, Any]:
    out = {k: r[k] for k in r.keys() if k != "data"}
    out.update(json.loads(r["data"]))
    out["label"] = KINDS[out["kind"]]
    out["status_label"] = STATUS[out["status"]]
    for k, label in (("role", "role_label"), ("from_role", "from_label")):
        if out.get(k):
            out[label] = roles.ROLE_LABELS.get(out[k], out[k])
    return out


def _flags(con, person_id: str) -> Dict[str, Any]:
    r = con.execute("select * from account_flags where person_id = ?", (person_id,)).fetchone()
    return dict(r) if r else {"person_id": person_id, "disabled": 0, "code": None, "code_exp": None}


def _set_flags(con, person_id: str, **f) -> None:
    cur = {**_flags(con, person_id), **f}
    con.execute(
        "insert or replace into account_flags values (?, ?, ?, ?)",
        (person_id, int(cur["disabled"]), cur["code"], cur["code_exp"]),
    )


def disabled(person_id: str) -> bool:
    with store._db() as con:
        r = con.execute("select disabled from account_flags where person_id = ?", (str(person_id),)).fetchone()
    return bool(r and r["disabled"])


def disabled_ids() -> set:
    with store._db() as con:
        return {r[0] for r in con.execute("select person_id from account_flags where disabled = 1")}


def seeded_ids() -> set:
    """The demo's personas: the seed's staff and clients (and their household members)."""
    ids = {s["id"] for s in store._seed_staff()["staff"]}
    for c in store._seed_clients():
        ids.add(c["id"])
    return ids


def protected(person_id: str) -> bool:
    return auth.demo_accounts_on() and person_id in seeded_ids()


def get(request_id: str) -> Dict[str, Any]:
    with store._db() as con:
        r = con.execute("select * from account_requests where id = ?", (str(request_id),)).fetchone()
    if r is None:
        raise KeyError(f"không có yêu cầu {request_id}")
    return _row(r)


def requests(limit: int = 40) -> List[Dict[str, Any]]:
    with store._db() as con:
        rows = con.execute(
            "select * from account_requests order by status = 'pending' desc, created desc limit ?", (limit,)
        ).fetchall()
    return [_row(r) for r in rows]


def _audit(by: str, action: str, rid: str, data: Dict[str, Any]) -> None:
    with control_db.tx() as con:
        audit.append(con, by, action, rid, data)


# -- the checks ---------------------------------------------------------------------------------


def _staff_account(con, person_id: str) -> Dict[str, Any]:
    r = con.execute(
        "select p.id, p.role, p.kind, p.name, a.login from people p join accounts a on a.person_id = p.id "
        "where p.id = ?",
        (person_id,),
    ).fetchone()
    if r is None:
        raise AccountError(f"Không có tài khoản {person_id!r}")
    if r["kind"] != "staff":
        raise AccountError("Tài khoản khách hàng không quản lý ở đây (đi cùng hồ sơ gia đình)")
    return {"id": r["id"], "role": r["role"], "name": store._open(r["name"], r["id"], "name"), "login": r["login"]}


def _enabled_admins(con) -> List[str]:
    rows = con.execute(
        "select p.id from people p join accounts a on a.person_id = p.id left join account_flags f on f.person_id "
        "= p.id where p.kind = 'staff' and p.role = 'admin' and coalesce(f.disabled, 0) = 0"
    ).fetchall()
    return [r[0] for r in rows]


def _check(con, kind: str, data: Dict[str, Any], by: str) -> Dict[str, Any]:
    """The request's data, normalised, or AccountError with why."""
    if kind not in KINDS:
        raise AccountError(f"Loại yêu cầu là một trong {', '.join(KINDS)}")
    if kind == "add":
        name = " ".join(str(data.get("name") or "").split())
        email = str(data.get("email") or "").strip().lower()
        role = str(data.get("role") or "")
        if len(name) < 2:
            raise AccountError("Cần họ tên")
        if not _EMAIL.match(email):
            raise AccountError("Cần email hợp lệ (là tên đăng nhập)")
        if role not in store.STAFF_ROLES:
            raise AccountError(f"Vai trò là một trong {', '.join(roles.ROLE_LABELS[r] for r in store.STAFF_ROLES)}")
        if con.execute("select 1 from accounts where login = ?", (email,)).fetchone():
            raise AccountError(f"Email {email} đã là tên đăng nhập của một tài khoản")
        title = str(data.get("title") or "").strip()[:80] or roles.ROLE_LABELS[role]
        return {"name": name, "email": email, "role": role, "title": title}
    pid = str(data.get("person_id") or "")
    if pid == by:
        raise AccountError("Không tự yêu cầu cho tài khoản của mình: nhờ một Quản trị khác")
    acc = _staff_account(con, pid)
    if protected(pid):
        raise AccountError(
            f"{acc['name']} là tài khoản demo: khi bật tài khoản demo, các tài khoản này được giữ nguyên để người "
            "xem sau vẫn vào được; chỉ tài khoản thêm ở trang này đổi được"
        )
    flags = _flags(con, pid)
    out = {"person_id": pid, "name": acc["name"], "from_role": acc["role"]}
    moving_off = kind == "disable" or (kind == "role" and data.get("role") != acc["role"])
    if kind == "role":
        role = str(data.get("role") or "")
        if role not in store.STAFF_ROLES:
            raise AccountError(f"Vai trò là một trong {', '.join(roles.ROLE_LABELS[r] for r in store.STAFF_ROLES)}")
        if role == acc["role"]:
            raise AccountError(f"{acc['name']} đã là {roles.ROLE_LABELS[role]}")
        out["role"] = role
    if kind == "disable" and flags["disabled"]:
        raise AccountError(f"{acc['name']} đã bị khoá")
    if kind == "enable" and not flags["disabled"]:
        raise AccountError(f"{acc['name']} đang mở")
    if kind == "reset" and flags["disabled"]:
        raise AccountError(f"{acc['name']} đang bị khoá: mở lại trước")
    if moving_off and acc["role"] == "rm":
        fams = store.families_of(pid)
        if fams:
            raise AccountError(
                f"{acc['name']} còn phụ trách {len(fams)} gia đình ({', '.join(fams)}): chuyển các gia đình cho RM "
                "khác ở Cấu hình › Phân công RM trước (hai người duyệt)"
            )
    if moving_off and acc["role"] == "admin" and _enabled_admins(con) == [pid]:
        raise AccountError("Đây là Quản trị cuối cùng còn mở: không khoá hay đổi vai trò được")
    return out


# -- requests and decisions --------------------------------------------------------------------


def request(kind: str, by: str, note: str = "", **data: Any) -> Dict[str, Any]:
    """A request from one Admin, waiting for another."""
    roles.require(by, "admin")
    now = time.time()
    auth._seeded()  # the accounts are seeded on first use (src/people/auth.py)
    store._assignment()  # the configuration seeds itself with its own write: before ours opens
    with store._db(write=True) as con:
        clean = _check(con, kind, data, by)
        open_ = con.execute(
            "select id from account_requests where status = 'pending' and (person_id = ? or json_extract(data, "
            "'$.email') = ?)",
            (clean.get("person_id") or "", clean.get("email") or ""),
        ).fetchone()
        if open_ is not None:
            raise Conflict(f"Đã có yêu cầu {open_['id']} đang chờ cho tài khoản này: duyệt hay rút nó trước")
        n = con.execute("select count(*) from account_requests").fetchone()[0] + 1
        rid = f"TK-{n:06d}"
        body = {**clean, "by": by, "note": str(note or "").strip()[:300]}
        con.execute(
            "insert into account_requests values (?, ?, ?, 'pending', ?, ?)",
            (rid, kind, clean.get("person_id"), now, json.dumps(body, ensure_ascii=False)),
        )
    _audit(by, "account.requested", rid, {"kind": kind, **{k: v for k, v in clean.items() if k != "name"}})
    return get(rid)


def decide(request_id: str, action: str, by: str, note: str = "") -> Dict[str, Any]:
    """Approve or reject (another Admin), or withdraw (the proposer). An approved add or reset answers its one-time
    code once (``code``); it is never stored or shown again."""
    if action not in ACTIONS:
        raise AccountError(f"action là một trong {', '.join(ACTIONS)}")
    roles.require(by, "admin")
    note = str(note or "").strip()[:300]
    applied = (None, None)  # (the person, a one-time code)
    auth._seeded()  # the accounts are seeded on first use (src/people/auth.py)
    store._assignment()  # the configuration seeds itself with its own write: before ours opens
    with store._db(write=True) as con:
        r = con.execute("select * from account_requests where id = ?", (str(request_id),)).fetchone()
        if r is None:
            raise KeyError(f"không có yêu cầu {request_id}")
        req = _row(r)
        if req["status"] != "pending":
            raise Conflict(f"Yêu cầu {req['id']} đã {req['status_label'].lower()}")
        if action == "withdraw" and by != req["by"]:
            raise roles.Forbidden("Chỉ người đề xuất rút được yêu cầu của mình")
        if action in ("approve", "reject") and by == req["by"]:
            raise roles.Forbidden("Người đề xuất không tự duyệt: cần một Quản trị khác (hai người)")
        if action == "approve" and by == req.get("person_id"):
            raise roles.Forbidden("Không duyệt yêu cầu về tài khoản của chính mình: cần một Quản trị khác")
        if action == "reject" and len(note) < 5:
            raise AccountError("Từ chối cần lý do")
        if action == "approve":
            _check(con, req["kind"], req, req["by"])  # again: the state may have moved since the request
            applied = _apply(con, req)
        status = {"approve": "approved", "reject": "rejected", "withdraw": "withdrawn"}[action]
        data = {**json.loads(r["data"]), "decided_by": by, "decided_at": time.time(), "decision_note": note}
        if req["kind"] == "add" and action == "approve":
            data["person_id"] = req["person_id"] = applied[0]
        con.execute(
            "update account_requests set status = ?, person_id = ?, data = ? where id = ?",
            (status, req.get("person_id"), json.dumps(data, ensure_ascii=False), req["id"]),
        )
    _audit(by, f"account.{status}", req["id"], {"kind": req["kind"], "person": req.get("person_id"), "note": note})
    out = get(req["id"])
    if applied[1]:
        out["code"], out["code_expires"] = applied[1], time.time() + CODE_TTL
    return out


def _code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(10))


def _hash(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()


def _apply(con, req: Dict[str, Any]) -> tuple:
    """The approved change, in the request's transaction: (the person's id, a new one-time code or None)."""
    kind, now = req["kind"], time.time()
    if kind == "add":
        seq = con.execute("select coalesce(max(seq), 0) from people").fetchone()[0] + 1
        n = 1 + sum(1 for _ in con.execute("select 1 from people where id like 'nv%'"))
        pid = f"nv{n:04d}"
        rec = {"id": pid, "role": req["role"], "name": req["name"], "email": req["email"], "title": req["title"]}
        con.execute(
            "insert into people values (?, ?, 'staff', ?, ?, ?, null, null, ?)",
            (pid, seq, req["role"], req["name"], req["email"], json.dumps(rec, ensure_ascii=False)),
        )
        con.execute("insert into accounts values (?, ?, null, ?, null)", (pid, req["email"], now))
        code = _code()
        _set_flags(con, pid, disabled=0, code=_hash(code), code_exp=now + CODE_TTL)
        return pid, code
    pid = req["person_id"]
    if kind == "role":
        r = con.execute("select data from people where id = ?", (pid,)).fetchone()
        rec = {**json.loads(store._open(r["data"], pid, "data")), "role": req["role"]}
        con.execute(
            "update people set role = ?, data = ? where id = ?", (req["role"], json.dumps(rec, ensure_ascii=False), pid)
        )
    elif kind == "disable":
        _set_flags(con, pid, disabled=1, code=None, code_exp=None)
    elif kind == "enable":
        _set_flags(con, pid, disabled=0)
    elif kind == "reset":
        code = _code()
        con.execute("update accounts set password = null where person_id = ?", (pid,))
        _set_flags(con, pid, code=_hash(code), code_exp=now + CODE_TTL)
        return pid, code
    return pid, None


def redeem(login: str, code: str, password: str) -> Optional[str]:
    """The person's id when the one-time code is theirs and fresh: their password is set and the code spent; else
    None (the same answer for an unknown login, a wrong, used or expired code)."""
    if len(password or "") < 8:
        raise AccountError("Mật khẩu cần ít nhất 8 ký tự")
    key = str(login or "").strip().lower()
    auth._seeded()  # the accounts are seeded on first use (src/people/auth.py)
    with store._db(write=True) as con:
        r = con.execute("select person_id from accounts where login = ? or lower(person_id) = ?", (key, key)).fetchone()
        if r is None:
            return None
        f = _flags(con, r["person_id"])
        fresh = f["code"] and (f["code_exp"] or 0) > time.time() and not f["disabled"]
        if not (fresh and hmac.compare_digest(f["code"], _hash(code or ""))):
            return None
        con.execute(
            "update accounts set password = ? where person_id = ?", (auth.hash_password(password), r["person_id"])
        )
        _set_flags(con, r["person_id"], code=None, code_exp=None)
    _audit(r["person_id"], "account.code_used", r["person_id"], {})
    return r["person_id"]


# -- the page's read ---------------------------------------------------------------------------


def read() -> Dict[str, Any]:
    """Tài khoản và vai trò (Admin): every staff account with its role, state and families (RMs), the requests
    (waiting first), whether the demo's accounts are protected."""
    off = disabled_ids()
    auth._seeded()  # the accounts are seeded on first use (src/people/auth.py)
    with store._db() as con:
        codes = {
            r[0]
            for r in con.execute(
                "select person_id from account_flags where code is not null and code_exp > ?", (time.time(),)
            )
        }
    seeded = seeded_ids()
    people = []
    for a in auth.accounts():
        if a["role"] == "client":
            continue
        people.append(
            {
                **a,
                "disabled": a["id"] in off,
                "code_waiting": a["id"] in codes,
                "families": store.families_of(a["id"]) if a["role"] == "rm" else None,
                "demo": a["id"] in seeded,
                "protected": protected(a["id"]),
            }
        )
    return {
        "people": people,
        "requests": requests(),
        "demo_protected": auth.demo_accounts_on(),
        "kinds": KINDS,
        "roles": {r: roles.ROLE_LABELS[r] for r in store.STAFF_ROLES},
    }

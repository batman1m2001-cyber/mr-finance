"""Sign-in (BRD-RULE-SEC-01, §13.1; owner 2026-10-16): every person has their own account, and only a verified
session is trusted.

- **Accounts.** Customers (and household members), RMs, CIOs, Compliance and Admin have accounts in
  ``accounts``. Specialists do not act in the app. A password is kept as a salted scrypt hash. Seeded accounts get
  ``MF_DEMO_PASSWORD`` when it is set; otherwise they have no password until one is set
  (``scripts/set_password.py``).
- **Session.** Signing in sets an HttpOnly cookie: the person's id and an expiry, signed with HMAC-SHA256. The
  key is ``MF_SESSION_SECRET``, or one generated once and kept in the state file, so every worker shares it.
- **Checks.** Inside a served run, :func:`signed_in` reads the cookie of the request that started it
  (``operonx.current_session``). :func:`control.roles.user` refuses an action whose ``by`` is not the person
  signed in, and :func:`require_client` refuses a family's data to anyone but that family and its assigned RM.
  Runs that no request started (scheduled jobs, the engine over every family, direct test runs) have no
  session and are not checked.
- **Demo accounts.** ``MF_DEMO_ACCOUNTS=on`` lists the accounts on the sign-in page and lets a visitor sign in
  as one with a click. It is meant for the public demo; a bank deployment turns it off and signs in through SSO
  instead of this form.
- ``MF_AUTH=off`` turns every check off. Only the ordinary test suite does that; ``tests/test_auth.py`` runs
  with it on.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from http.cookies import SimpleCookie
from typing import Any, Dict, List, Optional

from people import store

COOKIE = "mf_session"
TTL = 12 * 3600
ACCOUNT_ROLES = ("client", "rm", "cio", "compliance", "admin")


class NotSignedIn(PermissionError):
    """A served request without a valid session: answered 401."""

    http_status = 401


def enabled() -> bool:
    return (os.environ.get("MF_AUTH") or "on").strip().lower() not in ("off", "0", "false", "no")


def demo_accounts_on() -> bool:
    return (os.environ.get("MF_DEMO_ACCOUNTS") or "").strip().lower() in ("on", "1", "true", "yes")


# -- passwords and accounts ----------------------------------------------------------------------


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()


def check_password(password: str, stored: Optional[str]) -> bool:
    if not stored or not stored.startswith("scrypt$"):
        return False
    _, salt, dk = stored.split("$")
    got = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt), n=2**14, r=8, p=1, dklen=32)
    return hmac.compare_digest(got, base64.b64decode(dk))


def _ensure(con) -> None:
    """Seed the accounts once (the tables are made with the people's, src/people/store.py)."""
    if con.execute("select 1 from accounts limit 1").fetchone():
        return
    demo = os.environ.get("MF_DEMO_PASSWORD") or ""
    pw = hash_password(demo) if demo else None
    now = time.time()
    rows = con.execute("select id, kind, role, email from people order by seq").fetchall()
    for r in rows:
        if r["role"] not in ACCOUNT_ROLES:
            continue
        login = (r["email"] or r["id"]).lower()
        con.execute("insert into accounts values (?, ?, ?, ?, null)", (r["id"], login, pw, now))


def _db(write: bool = False):
    """Reads open no transaction: a check made inside another step's write (a config decision) must not wait on
    it. Only seeding and changes write."""
    return store._db(write=write)


def _seeded() -> None:
    with _db() as con:
        if con.execute("select 1 from accounts limit 1").fetchone():
            return
    with _db(write=True) as con:
        _ensure(con)


def accounts() -> List[Dict[str, Any]]:
    """Every account: who, their role, the login, whether a password is set."""
    _seeded()
    with _db() as con:
        rows = con.execute(
            "select a.person_id, a.login, a.password is not null as has_password, p.name, p.role, p.kind, "
            "p.member_of, p.data from accounts a join people p on p.id = a.person_id order by p.seq"
        ).fetchall()
    out = []
    for r in rows:
        data = json.loads(r["data"])
        out.append(
            {
                "id": r["person_id"],
                "login": r["login"],
                "has_password": bool(r["has_password"]),
                "name": r["name"],
                "role": r["role"],
                "title": data.get("title") or data.get("occupation") or "",
                "member_of": r["member_of"],
            }
        )
    return out


def set_password(person_id: str, password: str) -> None:
    if len(password) < 8:
        raise ValueError("mật khẩu cần ít nhất 8 ký tự")
    _seeded()
    with _db(write=True) as con:
        n = con.execute(
            "update accounts set password = ? where person_id = ?", (hash_password(password), person_id)
        ).rowcount
    if not n:
        raise KeyError(f"không có tài khoản {person_id!r}")


def reset() -> None:
    """Demo reset: the accounts go back to their seeds (the people are re-seeded first)."""
    with _db(write=True) as con:
        con.execute("delete from accounts")
        _ensure(con)


# -- sessions ----------------------------------------------------------------------------------


def _secret() -> bytes:
    env = os.environ.get("MF_SESSION_SECRET")
    if env:
        return env.encode("utf-8")
    with _db() as con:
        row = con.execute("select value from settings where key = 'session_secret'").fetchone()
    if row is None:
        with _db(write=True) as con:
            con.execute("insert or ignore into settings values ('session_secret', ?)", (secrets.token_hex(32),))
            row = con.execute("select value from settings where key = 'session_secret'").fetchone()
    return row["value"].encode("utf-8")


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def issue(person_id: str, now: Optional[float] = None) -> str:
    """A signed session for a person who has an account."""
    now = time.time() if now is None else now
    body = _b64(json.dumps({"sub": person_id, "iat": int(now), "exp": int(now + TTL)}).encode())
    sig = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify(token: Optional[str], now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """The person a session belongs to, or None when it is missing, forged, expired or their account is gone."""
    if not token or token.count(".") != 1:
        return None
    body, sig = token.split(".")
    want = _b64(hmac.new(_secret(), body.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, want):
        return None
    try:
        claims = json.loads(_unb64(body))
    except ValueError:
        return None
    if (time.time() if now is None else now) >= claims.get("exp", 0):
        return None
    return _account_person(str(claims.get("sub") or ""))


def _account_person(person_id: str) -> Optional[Dict[str, Any]]:
    _seeded()
    with _db() as con:
        row = con.execute("select 1 from accounts where person_id = ?", (person_id,)).fetchone()
    if row is None:
        return None
    p = store.person(person_id)
    if p is None:
        return None
    return _viewer(p)


def _viewer(p: Dict[str, Any]) -> Dict[str, Any]:
    """What the app needs to know about the person signed in."""
    out = {"id": p["id"], "name": p["name"], "role": p["role"], "title": p.get("title") or p.get("occupation") or ""}
    if p["role"] == "client":
        out["family"] = p.get("member_of") or p["id"]
    if p["role"] == "rm":
        out["families"] = store.families_of(p["id"])
    return out


def login(login_id: str, password: str) -> Optional[str]:
    """A session for the right login and password, else None (the same answer for an unknown login)."""
    key = str(login_id or "").strip().lower()
    _seeded()
    with _db() as con:
        row = con.execute(
            "select person_id, password from accounts where login = ? or lower(person_id) = ?", (key, key)
        ).fetchone()
    ok = row is not None and check_password(password or "", row["password"])
    if not ok:
        return None
    with _db(write=True) as con:
        con.execute("update accounts set last_login = ? where person_id = ?", (time.time(), row["person_id"]))
    return issue(row["person_id"])


def demo_login(person_id: str) -> Optional[str]:
    """A session for one listed demo account, only while ``MF_DEMO_ACCOUNTS`` is on."""
    if not demo_accounts_on():
        return None
    if _account_person(person_id) is None:
        return None
    return issue(person_id)


def from_cookie_header(cookie: Optional[str]) -> Optional[Dict[str, Any]]:
    if not cookie:
        return None
    jar = SimpleCookie()
    try:
        jar.load(cookie)
    except Exception:  # noqa: BLE001 — a malformed cookie header is no session
        return None
    morsel = jar.get(COOKIE)
    return verify(morsel.value) if morsel else None


# -- the checks inside a served run --------------------------------------------------------------


def _session() -> Any:
    """The request that started this run, or None when no request did (a schedule, a direct run)."""
    try:
        from operonx.app.serve.protocol import current_session
    except ImportError:  # pragma: no cover
        return None
    session = current_session()
    if session is None:
        return None
    meta = getattr(session, "meta", None) or {}
    if meta.get("trigger") == "schedule":
        return None
    return session


_UNSET = object()


def signed_in() -> Optional[Dict[str, Any]]:
    """The person signed in for the request that started this run (None: no request, or not signed in). Read once
    per request: a run over many families checks the cookie once."""
    session = _session()
    if session is None:
        return None
    cached = getattr(session, "_mf_viewer", _UNSET)
    if cached is not _UNSET:
        return cached
    headers = (getattr(session, "meta", None) or {}).get("headers") or {}
    viewer = from_cookie_header(headers.get("cookie"))
    try:
        session._mf_viewer = viewer
    except AttributeError:  # pragma: no cover — a session type that refuses attributes: read each time
        pass
    return viewer


def checking() -> bool:
    """Whether this run must be checked: sign-in is on and a request started it."""
    return enabled() and _session() is not None


def may_see(viewer: Dict[str, Any], client_id: str) -> bool:
    """A family's data: the family itself (and its household), its assigned RM, and the CIO, Compliance and
    Admin (who need it for runs, review and audit)."""
    cid = str(client_id or "")
    if viewer["role"] == "client":
        family = viewer["family"]
        try:
            head = store.client(cid).get("member_of") or cid
        except KeyError:
            return False
        return head == family
    if viewer["role"] == "rm":
        return store.assigned_rm(cid) == viewer["id"]
    return viewer["role"] in ("cio", "compliance", "admin")


def require_client(client_id: str) -> None:
    """Refuse a family's data to anyone who may not see it (inside a served run, sign-in on)."""
    if not checking():
        return
    from control.roles import Forbidden

    v = signed_in()
    if v is None:
        raise NotSignedIn("Cần đăng nhập")
    if not may_see(v, client_id):
        raise Forbidden(f"{v['name']} không được xem dữ liệu của khách hàng này")


def visible(client_ids: List[str]) -> List[str]:
    """The families of ``client_ids`` this run may read: all of them outside a checked request, else the ones the
    person signed in may see (a run over every family then reads only theirs)."""
    if not checking():
        return list(client_ids)
    v = signed_in()
    if v is None:
        return []
    return [c for c in client_ids if may_see(v, c)]


def role_for(asked: Optional[str]) -> Optional[str]:
    """The view a served read runs as. A customer always reads as ``client``. Staff read as their own role, or ask
    for the RM's or the client's view of what they may see. Outside a request: what was asked."""
    if not checking():
        return asked
    v = signed_in()
    if v is None:
        raise NotSignedIn("Cần đăng nhập")
    if v["role"] == "client":
        return "client"
    if asked in (v["role"], "client", "rm"):
        return asked
    return v["role"]


def acting_id(default: Optional[str] = None) -> Optional[str]:
    """Who acts in this request: the person signed in, else ``default`` (a direct run)."""
    if not checking():
        return default
    v = signed_in()
    return v["id"] if v else default

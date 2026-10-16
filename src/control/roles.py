"""Who may do what (BRD §13.1).

Every action names its user (``by``), and the server checks that user's role and the separation of duties. Inside
a request, ``by`` must be the person signed in (src/people/auth.py); in the bank the sign-in is SSO.
"""

from __future__ import annotations

from typing import Dict

SIGN_IN_ROLES = ("cio", "rm", "compliance", "admin", "specialist")


def users() -> Dict[str, Dict[str, str]]:
    """The staff who act in the app, by id (the people table, src/people): CIO, RM, Compliance, Admin and the
    specialists, who approve action recommendations for the families assigned to them (BRD-RULE-ROLE-05, G8)."""
    from people import store

    return {
        p["id"]: {"name": p["name"], "role": p["role"], "title": p["title"]}
        for p in store.staff()
        if p["role"] in SIGN_IN_ROLES
    }


ZONE_ACTOR = "agent:zone"  # who acts in the AI zone (app/zone.py): its jobs only, and only there


ROLE_LABELS = {
    "cio": "CIO",
    "rm": "RM",
    "compliance": "Tuân thủ",
    "admin": "Quản trị",
    "specialist": "Chuyên gia",
    "client": "Khách hàng",
}


class Forbidden(PermissionError):
    """The user's role may not do this. A served request answers 403 with the message (operonx ``http_status``)."""

    http_status = 403


def user(user_id: str) -> Dict[str, str]:
    """The staff user ``user_id``. Inside a request (sign-in on), it must be the person signed in: an action is
    never taken in someone else's name (BRD-RULE-SEC-01)."""
    from people import auth
    from wealth.paths import in_zone

    if in_zone() and user_id == ZONE_ACTOR and not auth.checking():
        return {"id": ZONE_ACTOR, "name": "Agent vùng AI", "role": "cio", "title": "Vùng AI (F-D7)"}
    if auth.checking():
        me = auth.signed_in()
        if me is None:
            raise auth.NotSignedIn("Cần đăng nhập")
        if me["id"] != str(user_id or ""):
            raise Forbidden(f"Đang đăng nhập là {me['name']}: không thể thao tác thay người khác")
    u = users().get(str(user_id or ""))
    if u is None:
        raise Forbidden(f"người dùng {user_id!r} không có trong demo")
    return {"id": str(user_id), **u}


def require(user_id: str, *roles: str) -> Dict[str, str]:
    """The user, when their role is one of ``roles``; else Forbidden."""
    u = user(user_id)
    if u["role"] not in roles:
        allowed = ", ".join(ROLE_LABELS[r] for r in roles)
        raise Forbidden(f"{u['name']} ({ROLE_LABELS[u['role']]}) không được làm việc này; cần vai trò: {allowed}")
    return u


def require_signed_in(*roles: str) -> None:
    """Inside a request (sign-in on), the person signed in holds one of ``roles``: for an action that names no
    ``by`` (fetching the news now). Outside a request (a scheduled job, a test), nothing to check."""
    from people import auth

    if not auth.checking():
        return
    me = auth.signed_in()
    if me is None:
        raise auth.NotSignedIn("Cần đăng nhập")
    if me["role"] not in roles:
        allowed = ", ".join(ROLE_LABELS[r] for r in roles)
        raise Forbidden(f"{me['name']} không được làm việc này; cần vai trò: {allowed}")

"""Who may do what (BRD §13.1), for the demo.

There is no sign-in here: the UI's role switcher sends a user id with each action, and the server
checks that user's role and the separation of duties by that id. That is NOT security — anyone can
send any id — and every screen that shows the switcher says so. In the bank this is SSO.
"""

from __future__ import annotations

from typing import Dict

USERS: Dict[str, Dict[str, str]] = {
    "cio": {"name": "Trần Quang Huy", "role": "cio", "title": "Giám đốc đầu tư (CIO)"},
    "cio2": {"name": "Lê Thu Hà", "role": "cio", "title": "Phó giám đốc đầu tư"},
    "rm01": {"name": "Phạm Gia Bảo", "role": "rm", "title": "Chuyên viên quan hệ khách hàng"},
    "compliance": {"name": "Đỗ Minh Châu", "role": "compliance", "title": "Tuân thủ (tuyến 2)"},
    "compliance2": {"name": "Vũ Hải Nam", "role": "compliance", "title": "Tuân thủ (tuyến 2)"},
    "admin": {"name": "Quản trị demo", "role": "admin", "title": "Quản trị"},
}

ROLE_LABELS = {"cio": "CIO", "rm": "RM", "compliance": "Tuân thủ", "admin": "Quản trị", "client": "Khách hàng"}


class Forbidden(PermissionError):
    """The user's role may not do this."""


def user(user_id: str) -> Dict[str, str]:
    u = USERS.get(str(user_id or ""))
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

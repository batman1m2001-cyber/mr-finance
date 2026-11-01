"""Admin's users and roles as steps (Q-25, src/people/accounts.py): file a request on a staff account, decide one.
Served through control/graph.py admin_flow (POST /api/accounts/request, /api/accounts/decide)."""

from operonx import op


@op
def file_request(kind: str, by: str, person_id: str = "", name: str = "", email: str = "", role: str = "",
                 title: str = "", note: str = "") -> dict:  # fmt: skip
    """One Admin asks: add an account, change a role, disable, enable, reset a password."""
    from people import accounts

    return {"request": accounts.request(kind, by, note, person_id=person_id, name=name, email=email, role=role,
                                        title=title)}  # fmt: skip


@op
def decide_request(request_id: str, action: str, by: str, note: str = "") -> dict:
    """Another Admin approves or rejects; the proposer withdraws. An approved add or reset answers its code once."""
    from people import accounts

    return {"request": accounts.decide(request_id, action, by, note)}

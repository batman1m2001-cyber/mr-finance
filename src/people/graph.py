"""Admin's users and roles as served steps (Q-25, src/people/accounts.py): account_request_flow (POST
/api/accounts/request) and account_decide_flow (POST /api/accounts/decide)."""

from operonx import END, START, graph, op


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


@graph
def account_request_flow(kind, by, person_id="", full_name="", email="", role="", title="", note=""):
    """A request on a staff account, waiting for a second Admin (``full_name``: ``name`` is the graph's own)."""
    done = file_request(kind=kind, by=by, person_id=person_id, name=full_name, email=email, role=role, title=title,
                        note=note)  # fmt: skip
    START >> done >> END


@graph
def account_decide_flow(request_id, action, by, note=""):
    """Approve, reject or withdraw a request on a staff account."""
    done = decide_request(request_id=request_id, action=action, by=by, note=note)
    START >> done >> END

"""policy_flow: one flow for the policy radar (FR-306), a route picks its `action` (app/main.py binds it with `variants`,
and `bodies.py` is each route's request contract).

add        POST /api/policy            a CIO adds a policy document
verify     POST /api/policy/verify     a second CIO confirms the document's source
status     POST /api/policy/status     a new status on the radar
summarise  POST /api/policy/summarise  the policy agent summarises a verified document"""

from operonx import END, START, graph
from operonx.core.ops import if_

from policy.ops import add, set_status, summarise, verify


@graph
def policy_flow(action="add", item=None, by=None, document_id=None, note="", status=None, date=None, mode=""):
    """The CIO's and the policy agent's writes on the radar."""
    added = add(item=item, by=by)
    verified = verify(document_id=document_id, by=by, note=note)
    set_ = set_status(document_id=document_id, status=status, by=by, note=note, date=date)
    summarised = summarise(document_id=document_id, by=by, mode=mode)
    a = action
    START >> if_(a == "verify", verified).if_(a == "status", set_).if_(a == "summarise", summarised).else_(added)
    added >> END
    verified >> END
    set_ >> END
    summarised >> END

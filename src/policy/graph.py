"""The policy radar's flows (POST /api/policy, /verify, /status, /summarise; FR-306)."""

from operonx import END, START, graph

from policy.ops import add, set_status, summarise, verify


@graph
def policy_add_flow(item, by):
    """A CIO adds a policy document."""
    done = add(item=item, by=by)
    START >> done >> END


@graph
def policy_verify_flow(document_id, by, note=""):
    """A second CIO confirms the document's source."""
    done = verify(document_id=document_id, by=by, note=note)
    START >> done >> END


@graph
def policy_status_flow(document_id, status, by, note="", date=None):
    """A new status on the radar."""
    done = set_status(document_id=document_id, status=status, by=by, note=note, date=date)
    START >> done >> END


@graph
def policy_summarise_flow(document_id, by, mode=""):
    """The policy agent summarises a verified document."""
    done = summarise(document_id=document_id, by=by, mode=mode)
    START >> done >> END

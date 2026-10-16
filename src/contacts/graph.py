"""contact_flow: an RM's contact with a family, recorded (POST /api/rm/contacts)."""

from operonx import END, START, graph

from contacts.ops import log_contact


@graph
def contact_flow(family_id, channel="call", signal=None, note=None, by=None):
    """An RM records a contact, from a Hôm nay signal or not (BRD-KPI-06)."""
    done = log_contact(family_id=family_id, channel=channel, signal=signal, note=note, by=by)
    START >> done >> END

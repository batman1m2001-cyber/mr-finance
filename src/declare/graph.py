"""declare_stream_flow: one chat turn said as it happens (POST /api/declare/stream, Accept: text/event-stream). The
plain turn (POST /api/declare) is statements/graph.py intake_flow, action declare."""

from operonx import END, START, graph
from operonx.app.serve import egress, ingress

from declare.ops import stream_declare


@graph
def declare_stream_flow():
    """The body is the one request (as POST /api/declare takes it); every event of the turn goes back at once."""
    src = ingress()
    ev = stream_declare(item=src["item"])
    out = egress(item=ev["event"])
    START >> src >> ev >> out >> END

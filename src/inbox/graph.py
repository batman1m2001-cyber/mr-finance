"""inbox_import_flow: the ``inbox_import`` job (every 10 minutes)."""

from operonx import END, START, graph

from inbox.ops import import_inbox


@graph
def inbox_import_flow(tick=None, at=None):
    """Every READY package from the AI zone, imported or rejected."""
    done = import_inbox(tick=tick, at=at)
    START >> done >> END

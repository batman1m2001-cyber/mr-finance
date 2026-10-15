"""config_propose_flow / config_decide_flow (POST /api/config/propose, /api/config/decide; FR-701)."""

from operonx import END, START, graph

from control.ops import decide, propose


@graph
def config_propose_flow(kind, data, by, note=""):
    """Propose a new version of one kind of configuration."""
    done = propose(kind=kind, data=data, by=by, note=note)
    START >> done >> END


@graph
def config_decide_flow(version_id, action, by, note=""):
    """Approve or reject a proposed version."""
    done = decide(version_id=version_id, action=action, by=by, note=note)
    START >> done >> END

"""The AI zone's jobs, one graph: TCB's push (every 10 minutes) and the zone's own tick (every 15 minutes) (F-D7)."""

from operonx import END, START, graph
from operonx.core.ops import if_

from zone.ops import push_sync, zone_tick


@graph
def zone_flow(action, tick=None, at=None):
    """``sync``: TCB → the AI zone, the approved catalogues and released research · ``agent``: the AI zone → TCB's
    inbox, one event's view, signed."""
    synced = push_sync(tick=tick, at=at)
    agent = zone_tick(tick=tick, at=at)
    START >> if_(action == "sync", synced).else_(agent)
    synced >> END
    agent >> END

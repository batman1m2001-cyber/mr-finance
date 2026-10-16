"""zone_sync_flow (TCB, every 10 minutes) and zone_agent_flow (the AI zone, every 15 minutes) (F-D7)."""

from operonx import END, START, graph

from zone.ops import push_sync, zone_tick


@graph
def zone_sync_flow(tick=None, at=None):
    """TCB → the AI zone: the approved catalogues and released research."""
    done = push_sync(tick=tick, at=at)
    START >> done >> END


@graph
def zone_agent_flow(tick=None, at=None):
    """The AI zone → TCB's inbox: one event's view, signed."""
    done = zone_tick(tick=tick, at=at)
    START >> done >> END

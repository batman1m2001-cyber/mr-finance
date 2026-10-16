"""The zone's jobs as ops: TCB's ``zone_sync`` (the catalogues out) and the zone's ``zone_agent`` (an event, run and
pushed)."""

from __future__ import annotations

from operonx import op

from zone import agent, sync


@op
def push_sync(tick: int = None, at: str = None) -> dict:
    """TCB: the approved catalogues and released research to the AI zone, when they changed (inbox mode only)."""
    return {"sync": sync.push()}


@op
async def zone_tick(tick: int = None, at: str = None) -> dict:
    """The AI zone: packages not delivered, again; then one event under the day's cap, run and pushed."""
    return {"zone": await agent.tick()}

"""The assistant's retention (A4, OWN-AS-15): the CIO's ``assistant_retention`` (two CIOs) says how many days a
conversation is kept after its last turn (default 365); the daily ``assistant_retention`` job deletes the older
ones — their turns, the model's side, parked runs — and the long-term items past their expiry (facts: 180 days).
What is deleted is gone: the pages are overwritten and the log emptied (``conversations.scrub``)."""

from __future__ import annotations

import time
from typing import Dict

from operonx.core.loggings import LOGGER

from assistant import conversations as conv
from assistant import attachments, memory
from control import audit, config, db

DAY = 86400.0


def days() -> int:
    return int(config.data("assistant_retention")["archive_days"])


async def sweep(now: float = None) -> Dict[str, int]:
    """Delete what is past retention; audited with the counts."""
    now = time.time() if now is None else now
    cut = now - days() * DAY
    with conv.db() as con:
        con.execute("begin immediate")
        old = [r[0] for r in con.execute("select id from conversations where updated < ?", (cut,)).fetchall()]
        turns = 0
        for cid in old:
            turns += conv.erase(con, cid)
        con.execute("commit")
    items = await memory.store().purge(now)
    out = {"conversations": len(old), "turns": turns, "memory_items": items, "attachments": attachments.sweep(now)}
    if any(out.values()):
        conv.scrub()
    with db.tx() as c:
        audit.append(c, "system", "assistant.retention", "-", {**out, "archive_days": days()})
    LOGGER.info("assistant retention: %s", out)
    return out

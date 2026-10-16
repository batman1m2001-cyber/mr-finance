"""The central structured log (BRD-NFR-12; BRD completion F7): one JSON object a line — time, level, process, event
and its fields — for what an operator looks for: alerts raised, acknowledged and resolved, job failures, the server's
own errors. Beside the state file (``mr-finance-log.jsonl``), or ``MF_LOG``; at 5 MB it moves to ``.1`` (one kept).
Both processes write it (the AI zone with ``process: zone``). It never holds a customer's data: callers pass ids
and error texts, not records."""

from __future__ import annotations

import json
import os
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

LEVELS = ("info", "warning", "error")
MAX_BYTES = 5 * 1024 * 1024


def path() -> Path:
    from wealth.paths import state_path

    return Path(os.environ.get("MF_LOG") or state_path().with_name("mr-finance-log.jsonl"))


def write(level: str, event: str, **fields: Any) -> None:
    """One line; a log that cannot be written never stops the work that logs."""
    from wealth.paths import in_zone

    rec = {"at": round(time.time(), 3), "level": level, "process": "zone" if in_zone() else "bank", "event": event}
    rec.update({k: v for k, v in fields.items() if v is not None})
    try:
        p = path()
        p.parent.mkdir(parents=True, exist_ok=True)
        if p.exists() and p.stat().st_size > MAX_BYTES:
            p.replace(p.with_name(p.name + ".1"))
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


def recent(limit: int = 50, level: Optional[str] = None) -> List[Dict[str, Any]]:
    """The newest lines first, at ``level`` or above."""
    p = path()
    if not p.exists():
        return []
    floor = LEVELS.index(level) if level in LEVELS else 0
    keep: deque = deque(maxlen=limit)
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("level") in LEVELS and LEVELS.index(rec["level"]) >= floor:
                keep.append(rec)
    return list(reversed(keep))

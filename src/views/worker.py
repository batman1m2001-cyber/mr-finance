"""The ops of the agent queue (views.queue): queue a run from the CIO's request, and the worker that runs it."""

from __future__ import annotations

from typing import Optional

from operonx import op

from views import queue


@op
def queue_agent(event_id: str, by: str = "cio", mode: Optional[str] = None) -> dict:
    """POST /api/events/run-agent: the run queued (or the one already waiting for this event)."""
    return {"job": queue.enqueue(event_id, by, mode)}


@op
async def work_queue(tick: int = None, at: str = None) -> dict:
    """The ``agent_worker`` job: the oldest queued run, through ``cio_agent_flow``."""
    return {"job": await run_next()}


async def run_next() -> Optional[dict]:
    from operonx import Operon

    from views.graph import cio_agent_flow

    job = queue.claim()
    if job is None:
        return None
    engine = Operon(cio_agent_flow, params={"event_id": None, "by": None, "mode": None})
    try:
        out = await engine.run(inputs={"event_id": job["event_id"], "by": job["by"], "mode": job["mode"]})
    except Exception as exc:  # noqa: BLE001 — a crash is a failed job the CIO sees, not a stuck one
        return queue.finish(job["id"], None, f"{type(exc).__name__}: {exc}"[:500])
    errors = out.get("$errors") or {}
    result = out.get("result") or {}
    view_id = (result.get("view") or {}).get("id")
    if errors or not view_id:
        first = next(iter(errors.values()), {}) if errors else {}
        why = first.get("reason") or str(first.get("message", "")).strip().splitlines()[-1:] or ["không ra nhận định"]
        return queue.finish(job["id"], view_id, why if isinstance(why, str) else why[0])
    return queue.finish(job["id"], view_id, None)

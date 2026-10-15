"""The daily accuracy job's step (FEAT-18): record the forecasts of any approved view not yet recorded, then
score every forecast whose horizon has passed against the stored market data."""

from __future__ import annotations

import asyncio

from operonx import op

from measure import forecasts


def _score(today: str = None) -> dict:
    return {"recorded": forecasts.record_missing(), **forecasts.score(today)}


@op
async def score_forecasts(today: str = None) -> dict:
    """Views approved → forecasts kept; forecasts due → scored (``today``: an ISO date, for a re-run)."""
    return {"scored": await asyncio.to_thread(_score, today)}

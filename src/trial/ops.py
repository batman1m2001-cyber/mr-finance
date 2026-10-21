"""The trial's steps: the morning run, and every 15 minutes the drafts' shadow forecasts kept, the due ones scored
and the day's report written to out/trial/<day>.json."""

from __future__ import annotations

import asyncio

from operonx import op

from trial import daily, report, shadow
from wealth.paths import ROOT

OUT = ROOT / "out" / "trial"


@op
async def trial_day(force: bool = False, tick: int = None, at: str = None) -> dict:
    """Group the news since the last run into events and run the agents on each (once a day; ``force`` again)."""
    return {"trial": await daily.run(force=bool(force))}


def _score(today: str = None) -> dict:
    got = {"recorded": daily.record_missing(), **shadow.score(today)}
    got["report"] = daily.write_day(str(OUT), report.summary())
    return got


@op
async def trial_score(today: str = None, tick: int = None, at: str = None) -> dict:
    """Trial drafts → shadow forecasts kept; the due ones scored; the report written."""
    return {"scored": await asyncio.to_thread(_score, today)}

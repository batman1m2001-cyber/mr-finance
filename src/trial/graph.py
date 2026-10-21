"""The trial's jobs (app/main.py schedules them; `operonx run trial_daily` runs the morning now)."""

from operonx import END, START, graph

from trial.ops import trial_day, trial_score


@graph
def trial_daily_flow(force=False, tick=None, at=None):
    """The news since the last run into events, the agents on each, their shadow forecasts kept."""
    done = trial_day(force=force, tick=tick, at=at)
    START >> done >> END


@graph
def trial_score_flow(today=None, tick=None, at=None):
    """The trial's shadow forecasts kept and scored, and its report written."""
    done = trial_score(today=today, tick=tick, at=at)
    START >> done >> END

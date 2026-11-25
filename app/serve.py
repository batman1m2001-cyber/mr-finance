"""What every app/<feature>.py shares: the port the product listens on, and the jobs' clock."""

import os

from operonx.app import env
from operonx.app import schedule as _schedule

PORT = env("PORT", 8030)


def schedule(**kw):
    """A job's clock — none with MF_JOBS=off (a second copy of the app, e.g. an experiment, runs no job on its
    own: no fetch and no model call twice; each still runs with `operonx run <job>`)."""
    return None if os.environ.get("MF_JOBS", "").lower() == "off" else _schedule(**kw)

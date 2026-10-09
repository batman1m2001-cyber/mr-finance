"""Where the fixtures and the state live."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("MF_DATA") or ROOT / "data")


def state_path() -> Path:
    """The SQLite file holding what clients added. ``MF_STATE`` moves it (tests use a tmp file)."""
    return Path(os.environ.get("MF_STATE") or DATA / "state.db")

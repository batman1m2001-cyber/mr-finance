"""Where the fixtures and the state live."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("MF_DATA") or ROOT / "data")


def state_path() -> Path:
    """The SQLite file holding what clients added. ``MF_STATE`` moves it (tests use a tmp file)."""
    return Path(os.environ.get("MF_STATE") or DATA / "state.db")


class OutsideTheZone(RuntimeError):
    """The AI zone (BRD-RULE-ZONE-01) holds no customer or staff data: reading it there is a bug, never a fallback."""


def in_zone() -> bool:
    """This process is the AI zone (``MF_ZONE=on``, app/zone.py): public news, released research and the approved
    catalogues only (F-D7)."""
    return (os.environ.get("MF_ZONE") or "").strip().lower() in ("1", "on", "true", "yes")


def no_people_in_zone(what: str) -> None:
    if in_zone():
        raise OutsideTheZone(f"Vùng AI không giữ dữ liệu khách hàng hay nhân sự (ZONE-01): {what}")

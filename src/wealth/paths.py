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


_SCHEMAS: set = set()


def _schema_key(con, path: Path, name: str):
    st = os.stat(path)
    # schema_version moves on any create or drop, so a file recreated at the same inode, or a table dropped, runs again
    return (str(path), st.st_dev, st.st_ino, con.execute("pragma schema_version").fetchone()[0], name)


def ensure_schema(con, path: Path, name: str, script: str) -> None:
    """Run a store's ``create … if not exists`` script once per database file and schema, not on every connection
    (NFR-01: a connection plus a query took 0.81 ms with the script, 0.58 ms without, at 6,500 families)."""
    if _schema_key(con, path, name) in _SCHEMAS:
        return
    con.executescript(script)
    _SCHEMAS.add(_schema_key(con, path, name))


def forget_schema() -> None:
    _SCHEMAS.clear()

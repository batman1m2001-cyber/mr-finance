"""Every test gets an empty state file of its own, the project's resources, and the rule paths
(MF_AI=off) unless it turns the model on itself. Sign-in is off (MF_AUTH=off) except in tests/test_auth.py and the
browser tests, which sign in."""

from pathlib import Path

import operonx
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def resources():
    operonx.bootstrap(resources=str(ROOT / "resources.yaml"))


@pytest.fixture(autouse=True)
def state(tmp_path, monkeypatch):
    path = tmp_path / "state.db"
    monkeypatch.setenv("MF_STATE", str(path))
    monkeypatch.setenv("MF_AI", "off")
    monkeypatch.setenv("MF_AUTH", "off")
    return path

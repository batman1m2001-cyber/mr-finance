"""Every test gets an empty state file of its own: what one test adds, no other sees."""

import pytest


@pytest.fixture(autouse=True)
def state(tmp_path, monkeypatch):
    path = tmp_path / "state.db"
    monkeypatch.setenv("MF_STATE", str(path))
    return path

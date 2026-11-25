"""Every test gets an empty state file of its own, the project's resources, and the rule paths
(MF_AI=off) unless it turns the model on itself. The run post-check's "today" is the fixture prices' own date, so
a run is not held for stale prices as the calendar moves past data/market.json. Sign-in is off (MF_AUTH=off)
except in tests/test_auth.py and the browser tests, which sign in. Traces are local, in the test's folder."""

import json
from datetime import date
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
    # traces go to this test's folder, never the project's run store (operonx.toml [tracing]): OPERONX_TRACE stands
    # where [tracing] sinks does, read each time a service or job settles
    monkeypatch.setenv("OPERONX_TRACE", "local")
    monkeypatch.setenv("OPERONX_RUNS_DIR", str(tmp_path / "runs"))
    return path


PRICE_DATE = date.fromisoformat(json.loads((ROOT / "data" / "market.json").read_text())["as_of"])


class _PriceDay(date):
    @classmethod
    def today(cls):
        return PRICE_DATE


@pytest.fixture(autouse=True)
def price_day(monkeypatch):
    import apply.run

    monkeypatch.setattr(apply.run, "date", _PriceDay)

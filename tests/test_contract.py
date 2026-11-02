"""Every route and job keeps its contract while the flows are merged (docs/FEATURE_FLOWS_PLAN.md, FF0): the method,
the path, the fields a request may and must carry, the clock of each job, and the shape of the read-only replies.
tests/data/contract.json is written by `uv run python scripts/pin_contract.py`; change it only when a route
is meant to change, never to make a refactor pass."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pin_contract import contract  # noqa: E402

PINNED = json.loads((ROOT / "tests" / "data" / "contract.json").read_text())
LIVE, _ = contract()


def test_no_route_or_job_was_added_or_dropped():
    assert sorted(LIVE["services"]) == sorted(PINNED["services"])
    assert sorted(LIVE["jobs"]) == sorted(PINNED["jobs"])


def test_each_route_keeps_its_method_path_and_request_fields():
    for name, want in PINNED["services"].items():
        got = LIVE["services"][name]
        assert (got["kind"], got["method"], got["path"]) == (want["kind"], want["method"], want["path"]), name
        # a route's body contract: the fields it accepts, which are required, and their defaults (D1)
        assert got["fields"] == want["fields"], name


def test_each_job_keeps_its_clock():
    assert LIVE["jobs"] == PINNED["jobs"]


def test_the_read_only_pages_answer_with_the_same_keys():
    assert LIVE["responses"] == PINNED["responses"]

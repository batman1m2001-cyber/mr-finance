"""Every op declares the stores it reaches (scripts/stores.py): the picture draws flow → store → flow from it."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_op_declares_the_stores_its_sql_reaches():
    done = subprocess.run([sys.executable, "scripts/stores.py"], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stdout[-2000:]

"""Seal the client data under the current key (BRD-NFR-07, src/control/crypto.py).

    python scripts/rotate_keys.py --check     # how many values each key seals, how many are plain
    python scripts/rotate_keys.py             # every value opened and sealed again under the first key of
                                              # MF_DATA_KEYS; plain values sealed; one transaction
    python scripts/rotate_keys.py --new k2    # a fresh key entry to put first in MF_DATA_KEYS (printed: for the
                                              # operator's secret store, never a log)

Rotation: ``--new k2``, put ``k2=…`` first in MF_DATA_KEYS (the secret store, a file or .env), restart, run this,
``--check`` until ``k1`` holds nothing, then remove ``k1``. Works on the database ``MF_STATE`` names (default
data/state.db); a server may keep running: the rotation is one write transaction.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from control import crypto  # noqa: E402
from wealth.paths import state_path  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--new", metavar="KEY_ID")
    a = ap.parse_args()
    if a.new:
        print(f"{a.new}={crypto.new_key()}")
        return
    con = sqlite3.connect(state_path(), timeout=30, isolation_level=None)
    try:
        if a.check:
            print(json.dumps(crypto.census(con)))
            return
        con.execute("begin immediate")
        out = crypto.rotate(con)
        con.execute("commit")
        print(json.dumps({"key": crypto.current(), "written": out, "now": crypto.census(con)}))
    finally:
        con.close()


if __name__ == "__main__":
    main()

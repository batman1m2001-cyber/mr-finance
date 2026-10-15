"""Ask every market source for its last few days, live, and say what answered (F1, F-D2). The suite never touches
the network; this is the check (on the shipped list, data/market_sources.json) that the sources
still answer in the format the adapters read. Nothing is stored.

    uv run python scripts/market_smoke.py [--days 7]
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / "src")]

import json  # noqa: E402

from market import sources  # noqa: E402

CATALOGUE = Path(__file__).resolve().parents[1] / "data" / "market_sources.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    end = date.today()
    start = end - timedelta(days=args.days)
    bad = 0
    for spec in json.loads(CATALOGUE.read_text(encoding="utf-8"))["series"]:  # the shipped list, no state file
        for s in spec["sources"]:
            t0 = time.time()
            try:
                got = sources.ADAPTERS[s["source"]](
                    s["symbol"], start, end, sources.http, scale=float(s.get("scale", 1))
                )
                last = got.points[-1] if got.points else None
                status = f"{len(got.points):3d} points, last {last}" if last else "  0 points"
                bad += not got.points
            except Exception as exc:  # noqa: BLE001 — report and go on
                status, bad = f"FAILED {type(exc).__name__}: {str(exc)[:80]}", bad + 1
            print(f"{spec['id']:<18} {s['source']:<9} {time.time() - t0:5.1f}s  {status}")
    print(f"\n{bad} source(s) without points")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

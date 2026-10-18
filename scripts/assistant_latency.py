"""Where the assistant's time goes, read back from the audit log (each `assistant.turn` keeps its timing in ms, no
words: `assistant.stream.Clock`). Median and p90 per phase, for turns that called tools and turns that did not.

    .venv/bin/python scripts/assistant_latency.py                      # data/state.db, every turn with a timing
    .venv/bin/python scripts/assistant_latency.py --state <copy>/state.db --since 2026-10-18
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent


def pct(xs: List[float], q: float) -> float:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(len(xs) * q))]


def phases(t: Dict) -> Dict[str, float]:
    """One turn's phases (s): before the first model call; for a tool turn the first call (until its tool calls),
    the tools, and the answer's call until its first words; the answer's writing; the first words the person saw
    (from the turn's start); the whole turn."""
    calls = t["calls"]
    out = {"before_model": (t.get("start") or 0) / 1000}
    if len(calls) > 1:
        out["tool_call"] = calls[0][1] / 1000
        out["tools"] = t["tools"] / 1000
    first, end = calls[-1]
    out["answer_wait"] = (first or 0) / 1000
    out["writing"] = (end - (first or 0)) / 1000
    if t.get("first_text") is not None:
        out["first_words"] = t["first_text"] / 1000
    out["total"] = t["total"] / 1000
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=str(ROOT / "data" / "state.db"))
    ap.add_argument("--since", default="", help="YYYY-MM-DD: only turns from that day on")
    a = ap.parse_args()
    since = datetime.fromisoformat(a.since).timestamp() if a.since else 0
    con = sqlite3.connect(f"file:{a.state}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "select data from audit_log where action = 'assistant.turn' and ts >= ? order by seq", (since,)
    ).fetchall()
    groups: Dict[str, List[Dict[str, float]]] = {"tool turns": [], "no-tool turns": []}
    for r in rows:
        t = json.loads(r["data"]).get("timing")
        if t and t.get("calls"):
            groups["tool turns" if len(t["calls"]) > 1 else "no-tool turns"].append(phases(t))
    if not any(groups.values()):
        sys.exit("no timed assistant turns in " + a.state)
    for name, ps in groups.items():
        if not ps:
            continue
        print(f"{name}: {len(ps)}")
        for k in ps[0]:
            xs = [p[k] for p in ps if k in p]
            print(f"  {k:<13} median {statistics.median(xs):5.2f} s   p90 {pct(xs, 0.9):5.2f} s")


if __name__ == "__main__":
    main()

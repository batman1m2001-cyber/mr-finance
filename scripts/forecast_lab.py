"""The forecast lab's table (FORECAST_DESK_PLAN): each track's direction when it calls (with its week-block 95%
interval), against the fair baselines on the same calls and the hindsight bar, the recall of big moves and the
amount — on the dev replays or the test one, never both mixed.

    uv run python scripts/forecast_lab.py --set dev                  # the July and August replays
    uv run python scripts/forecast_lab.py --set test --track desk    # the test replay, once

A track other than the agents' and the baselines is read from out/lab/tracks/<track>/<replay>.json
({"<morning>|<horizon>|<factor>": expected move in the factor's unit}). The market data is the live state's,
copied to out/lab/market.db (the live file is never opened for writing).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETS = {"dev": ("2026-07", "2026-08"), "test": ("2026-09",)}
LAB = ROOT / "out" / "lab"


def market() -> Path:
    LAB.mkdir(parents=True, exist_ok=True)
    path = LAB / "market.db"
    src = sqlite3.connect(f"file:{ROOT / 'data' / 'state.db'}?mode=ro", uri=True)
    dst = sqlite3.connect(path)
    src.backup(dst)
    src.close()
    dst.close()
    return path


def pct(x) -> str:
    return "   –" if x is None else f"{100 * x:3.0f}%"


def frac(m) -> str:
    return f"{pct(m['value'])} {m['hits']:>3}/{m['n']:<3}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--set", choices=SETS, default="dev")
    ap.add_argument("--track", action="append", default=[], help="a stored track to score beside the agents")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--json", help="write the table's numbers here too")
    a = ap.parse_args()
    os.environ["MF_STATE"] = str(market())
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from measure import realised
    from trial import lab

    series = realised.series()
    played = [n for n in SETS[a.set] if (ROOT / "out" / "replay" / n / "replay.json").exists()]
    universe = [r for n in played for r in lab.moves(ROOT / "out" / "replay" / n / "state.db")]
    fair = {"momentum": lab.baseline(lab.momentum, universe, series),
            "majority60": lab.baseline(lab.majority, universe, series)}
    tracks = {"agents": universe, **{n: lab.judge(t, universe, series) for n, t in fair.items()}}
    for name in a.track:
        t = {}
        for replay in played:
            path = LAB / "tracks" / name / f"{replay}.json"
            t.update({tuple(k.split("|")): v for k, v in json.loads(path.read_text()).items()})
        tracks[name] = lab.judge(t, universe, series)
    out = {}
    print(f"set {a.set}: {', '.join(played)} (of {', '.join(SETS[a.set])})")
    for h in lab.HORIZONS:
        print(f"\n{h:<11} {'direction on calls':<30} {'hindsight':<13} {'momentum':<17} {'majority60':<17} "
              f"{'recall big':<13} {'big→big':<13} {'said big→big':<13} IC")
        for name, rows in tracks.items():
            got = lab.report([r for r in rows if r["horizon"] == h], {k: v for k, v in fair.items() if k != name},
                             a.boot)
            out[f"{name}:{h}"] = got
            lo, hi = got["interval"]
            ci = f"[{pct(lo)}–{pct(hi)}]" if lo is not None else ""
            f = got["fair"]
            vs = lambda k: f"{frac(f[k])} p{f[k]['p']:.2f}" if k in f and f[k]["p"] is not None else "–"  # noqa: E731
            print(f"{name:<11} {frac(got['call_direction'])} {ci:<14} {frac(got['hindsight']):<13} {vs('momentum'):<17} "
                  f"{vs('majority60'):<17} {frac(got['recall']):<13} {frac(got['amount_recall']):<13} "
                  f"{frac(got['amount_precision']):<13} {got['ic']}")
    if a.json:
        Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

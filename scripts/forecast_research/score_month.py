"""One dev month's measures per track (lab.judge + lab.measures), per horizon. Usage: score_month.py MONTH TRACK..."""
import json, os, sys
from pathlib import Path
os.environ["MF_STATE"] = "out/lab/market.db"
sys.path[:0] = ["src", "."]
from measure import realised
from trial import lab
mon = sys.argv[1]; assert mon != "2026-09", "never the test month"
S = realised.series(); U = lab.moves(Path(f"out/replay/{mon}/state.db"))
f = lambda d: f"{d['value'] if d['value'] is None else round(100*d['value'])}% {d['hits']}/{d['n']}"
for h in ("3d", "1w"):
    u = [r for r in U if r["horizon"] == h]
    print(f"\n{mon} {h}")
    for name in ["agents"] + sys.argv[2:]:
        if name == "agents":
            m = lab.measures(u)
        else:
            t = {tuple(k.split("|")): v for k, v in json.loads(Path(f"out/lab/tracks/{name}/{mon}.json").read_text()).items()}
            t = {k: v for k, v in t.items() if v}
            m = lab.measures(lab.judge(t, u, S))
        print(f"  {name:12} dir {f(m['call_direction']):14} hind {m['hindsight']}  recall {f(m['recall']):12} "
              f"big→big {f(m['amount_recall']):12} said→big {f(m['amount_precision']):12} ic {m['ic']}")

"""Dev on the calendar for the knowledge base: each morning 2026-07-01.. (due by 2026-09-21), that day's headlines'
analogs (2024-01 .. the origin) against each factor's realised move in σ. Run from the fi worktree."""
import math, os, pickle, sys, time
from collections import defaultdict
from pathlib import Path
os.environ["MF_STATE"] = "out/lab/market.db"
sys.path[:0] = ["src", "."]
from measure import realised
from trial import kb, lab, shadow

S = realised.series()
m = shadow.model()
feeds = Path("out/replay/feeds")
t = time.time()
base = kb.load(feeds, "2024-01-01", "2026-09-21")
print("docs", len(base.docs), round(time.time() - t), "s")
LAST = "2026-09-21"
K = int(sys.argv[1]) if len(sys.argv) > 1 else 20
rows = []
day = "2026-07-01"
while shadow.realised.add_days(day, 6) <= LAST:
    origin = shadow.realised.add_days(day, -1)
    texts = [ti for _, ti in kb.headlines(feeds, day, day)]
    if texts:
        for h in ("3d", "1w"):
            n = shadow.HORIZON_DAYS[h]
            if shadow.realised.add_days(origin, n) > LAST:
                continue
            an = kb.analogs(base, texts, origin, h, S, m, k=K)
            for fid, s in S.items():
                y = s.move(origin, shadow.realised.add_days(origin, n))
                if not y or fid not in an:
                    continue
                rows.append(dict(h=h, fid=fid, d=day, z=y / (m.factor(fid).vol_month * math.sqrt(m.horizons[h])),
                                 mean=an[fid]["mean"], up=an[fid]["up"], days=an[fid]["days"]))
    day = shadow.realised.add_days(day, 1)
print("scored", round(time.time() - t), "s")
pickle.dump(rows, open(Path(__file__).with_name(f"analog_rows_{K}.pkl"), "wb"))
for h in ("3d", "1w"):
    R = [r for r in rows if r["h"] == h]
    z = [r["z"] for r in R]
    print(f"\n{h}: n={len(R)}  IC mean {lab.spearman([r['mean'] for r in R], z)}  IC up {lab.spearman([r['up'] for r in R], z)}")
    by = defaultdict(list)
    for r in R: by[r["fid"]].append(r)
    for fid, xs in sorted(by.items()):
        zz = [r["z"] for r in xs]
        print(f"  {fid:14} n={len(xs):3}  IC mean {lab.spearman([r['mean'] for r in xs], zz)}  IC up {lab.spearman([r['up'] for r in xs], zz)}")

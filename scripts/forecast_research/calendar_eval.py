"""Dev on the calendar: every factor, every origin 2026-07-01 .. (due by 2026-09-21), the odds' P(up)/P(big) and
momentum against the realised move in σ. Per factor IC, and selective accuracy. Run from the fi worktree."""
import math, os, pickle, sys, time
from collections import defaultdict
from pathlib import Path
os.environ["MF_STATE"] = "out/lab/market.db"
sys.path[:0] = ["src", "."]
from measure import realised
from trial import lab, odds, shadow

S = realised.series()
m = shadow.model()
cache = Path(__file__).with_name("odds_cal.pkl")
if cache.exists():
    O = odds.Odds.__new__(odds.Odds); O.__dict__.update(pickle.loads(cache.read_bytes())); O.series = S
else:
    t = time.time(); O = odds.Odds(S); print("trained", round(time.time() - t), "s")
    cache.write_bytes(pickle.dumps({k: v for k, v in O.__dict__.items() if k != "series"}))
LAST = "2026-09-21"
rows = []
for h in ("3d", "1w"):
    n = shadow.HORIZON_DAYS[h]; sc = lambda f: m.factor(f).vol_month * math.sqrt(m.horizons[h])
    d = "2026-07-01"
    while shadow.realised.add_days(d, n) <= LAST:
        for fid, s in S.items():
            y = s.move(d, shadow.realised.add_days(d, n))
            if not y: continue
            got = O.of(fid, d, h)
            if not got: continue
            f = got["features"]
            rows.append(dict(h=h, fid=fid, d=d, z=y / sc(fid), pu=got["p_up"], pb=got["p_big"],
                             mom=f["m3d" if h == "3d" else "m1w"], **{k: v for k, v in f.items()}))
        d = shadow.realised.add_days(d, 1)
pickle.dump(rows, open(Path(__file__).with_name("cal_rows.pkl"), "wb"))

def auc(score, label):
    pos = [s for s, l in zip(score, label) if l]; neg = [s for s, l in zip(score, label) if not l]
    if not pos or not neg: return None
    return round(sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / (len(pos) * len(neg)), 2)

for h in ("3d", "1w"):
    R = [r for r in rows if r["h"] == h]
    print(f"\n{h}: n={len(R)}  IC p_up {lab.spearman([r['pu'] for r in R], [r['z'] for r in R])}"
          f"  momentum {lab.spearman([r['mom'] for r in R], [r['z'] for r in R])}"
          f"  AUC p_big {auc([r['pb'] for r in R], [abs(r['z']) >= 1 for r in R])}"
          f"  |mom| {auc([abs(r['mom']) for r in R], [abs(r['z']) >= 1 for r in R])}  big share {sum(abs(r['z'])>=1 for r in R)/len(R):.2f}")
    by = defaultdict(list)
    for r in R: by[r["fid"]].append(r)
    for fid, xs in sorted(by.items()):
        z = [r["z"] for r in xs]
        print(f"  {fid:14} n={len(xs):3}  up {sum(x>0 for x in z)/len(z):.2f}  IC p_up {lab.spearman([r['pu'] for r in xs], z)}"
              f"  mom {lab.spearman([r['mom'] for r in xs], z)}  acc p_up {sum((r['pu']>.5)==(r['z']>0) for r in xs)/len(xs):.2f}"
              f"  acc mom {sum((r['mom']>0)==(r['z']>0) for r in xs)/len(xs):.2f}")

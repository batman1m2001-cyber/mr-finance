"""In-sample (2020-04 → 2026-06 only) rank correlation of candidate features with the next move, per factor."""
import os, sys, math
os.environ["MF_STATE"] = "out/lab/market.db"; sys.path[:0] = ["src", "."]
from datetime import date, timedelta
from measure import realised
from trial import shadow, lab
S = realised.series(); m = shadow.model()
back = lambda d, n: (date.fromisoformat(d) - timedelta(days=n)).isoformat()
add = realised.add_days
def sig(f, n): return m.factor(f).vol_month * math.sqrt(n / 30.4375)
cands = {
 "own1d": lambda f, o: S[f].move(back(o, 1), o) / sig(f, 1) if S[f].move(back(o, 1), o) is not None else None,
 "own1w": lambda f, o: (S[f].move(back(o, 7), o) or 0) / sig(f, 7),
 "own1m": lambda f, o: (S[f].move(back(o, 30), o) or 0) / sig(f, 30),
 "eq1d": lambda f, o: (S["GLOBAL_EQ"].move(back(o, 1), o) or 0) / sig("GLOBAL_EQ", 1),
 "eq1w": lambda f, o: (S["GLOBAL_EQ"].move(back(o, 7), o) or 0) / sig("GLOBAL_EQ", 7),
 "dxy1w": lambda f, o: (S["DXY"].move(back(o, 7), o) or 0) / sig("DXY", 7),
 "btc1d": lambda f, o: (S["BTC"].move(back(o, 1), o) or 0) / sig("BTC", 1),
}
for h, n in (("3d", 3), ("1w", 7)):
    print("==", h)
    for f in sorted(S):
        ys, X = [], {k: [] for k in cands}
        o = "2020-04-01"
        while add(o, n) <= "2026-06-30":
            y = S[f].move(o, add(o, n))
            if y:
                vals = {k: c(f, o) for k, c in cands.items()}
                if all(v is not None for v in vals.values()):
                    ys.append(y)
                    for k in cands: X[k].append(vals[k])
            o = add(o, 3)
        print(f"{f:<13} n={len(ys):<4}", " ".join(f"{k}={lab.spearman(X[k], ys) or 0:+.2f}" for k in cands))

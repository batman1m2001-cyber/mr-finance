"""Dev evidence for the odds: IC of P(up) and of momentum, accuracy, AUC of P(big). Run from the fi worktree."""
import os, sys, time
from pathlib import Path
os.environ["MF_STATE"] = "out/lab/market.db"
sys.path[:0] = ["src", "."]
from measure import realised
from trial import lab, odds

def auc(score, label):
    pos = [s for s, l in zip(score, label) if l]; neg = [s for s, l in zip(score, label) if not l]
    if not pos or not neg: return None
    return round(sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg)), 3)

S = realised.series()
t = time.time()
last = sys.argv[1] if len(sys.argv) > 1 else "2026-06-30"
O = odds.Odds(S, last=last)
print("trained", round(time.time() - t, 1), "s; big base rate", O.base)
names = [n for n in ("2026-07", "2026-08") if Path(f"out/replay/{n}/replay.json").exists()]
U = [r for n in names for r in lab.moves(Path(f"out/replay/{n}/state.db"))]
for h in ("3d", "1w"):
    R = [r for r in U if r["horizon"] == h and r["verdict"] in lab.SCORED and r.get("realised")]
    got = [(r, O.of(r["factor"], r["origin"], h), lab.momentum(r, S)) for r in R]
    got = [g for g in got if g[1]]
    z = [g[0]["realised"] / g[0]["scale"] for g in got]
    pu = [g[1]["p_up"] for g in got]; pb = [g[1]["p_big"] for g in got]
    mom = [(g[2] or 0) / g[0]["scale"] for g in got]
    ai = [(g[0].get("expected") or 0) / g[0]["scale"] for g in got]
    acc = sum((p > .5) == (x > 0) for p, x in zip(pu, z)) / len(z)
    ups = sum(x > 0 for x in z) / len(z)
    conf = [(p, x) for p, x in zip(pu, z) if abs(p - .5) >= .05]
    print(f"{h} {names} n={len(z)}  IC odds {lab.spearman(pu, z)}  momentum {lab.spearman(mom, z)}  AI {lab.spearman(ai, z)}"
          f" | acc odds {acc:.2f} (up share {ups:.2f}); |p-.5|>=.05: {sum((p>.5)==(x>0) for p,x in conf)}/{len(conf)}"
          f" | AUC p_big {auc(pb, [abs(x) >= 1 for x in z])}  |mom| {auc([abs(v) for v in mom], [abs(x) >= 1 for x in z])}"
          f"  |AI| {auc([abs(v) for v in ai], [abs(x) >= 1 for x in z])}")

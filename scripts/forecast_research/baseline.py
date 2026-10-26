"""What simple market statistics do on the replays' scored moves, beside the AI. Run from ~/mr-finance."""
import json, os, sqlite3, sys
from datetime import date, timedelta
sys.path.insert(0, "src")

def back(d, n): return (date.fromisoformat(d) - timedelta(days=n)).isoformat()
def pct(k, n): return f"{100*k/n:4.0f}% ({k}/{n})" if n else "   –"

def spearman(a, b):
    import statistics
    ra = {i: r for r, i in enumerate(sorted(range(len(a)), key=lambda i: a[i]))}
    rb = {i: r for r, i in enumerate(sorted(range(len(b)), key=lambda i: b[i]))}
    x = [ra[i] for i in range(len(a))]; y = [rb[i] for i in range(len(b))]
    return statistics.correlation(x, y) if len(a) > 2 else None

for name in sys.argv[1:]:
    os.environ["MF_STATE"] = f"out/replay/{name}/state.db"
    import importlib
    from measure import realised; importlib.reload(realised)
    S = realised.series()
    c = sqlite3.connect(os.environ["MF_STATE"])
    for h, nd in (("1w", 7), ("3d", 3)):
        R = [json.loads(d) | {"factor": f} for f, d in c.execute("select factor, data from eval_scores where horizon=?", (h,))]
        R = [r for r in R if r["verdict"] in ("correct", "incorrect", "missed", "quiet") and r.get("ran") and r.get("realised")]
        for r in R:
            s = S.get(r["factor"]); o = r["origin"]
            r["mom"] = s.move(back(o, nd), o) if s else None
            r["mom1m"] = s.move(back(o, 30), o) if s else None
            r["big"] = abs(r["realised"]) >= r["material_sigma"] * r["scale"]
        def acc(rows, pred):
            k = n = 0
            for r in rows:
                p = pred(r)
                if p in (None, 0): continue
                n += 1; k += (p > 0) == (r["realised"] > 0)
            return pct(k, n)
        calls = [r for r in R if r.get("claim") in ("up", "down")]
        ai = lambda r: 1 if r.get("claim") == "up" else -1 if r.get("claim") == "down" else None
        print(f"\n{name} {h}: {len(R)} moves, AI calls {len(calls)}")
        print("  direction on the AI's calls:  AI", acc(calls, ai), "| momentum (same horizon)", acc(calls, lambda r: r["mom"]),
              "| momentum 1m", acc(calls, lambda r: r["mom1m"]), "| reversal", acc(calls, lambda r: -r["mom"] if r["mom"] else None))
        print("  direction on all moves:       AI expected", acc(R, lambda r: r.get("expected")), "| momentum", acc(R, lambda r: r["mom"]),
              "| momentum 1m", acc(R, lambda r: r["mom1m"]))
        bigs = [r for r in R if r["big"]]
        print("  direction on big moves:       AI expected", acc(bigs, lambda r: r.get("expected")), "| momentum", acc(bigs, lambda r: r["mom"]),
              "| momentum 1m", acc(bigs, lambda r: r["mom1m"]))
        ex = [r for r in R if r.get("expected") is not None]
        z = lambda r, k: r[k] / r["scale"]
        print("  size ranking (spearman |pred| vs |real|, in σ):  AI", round(spearman([abs(z(r,'expected')) for r in ex], [abs(z(r,'realised')) for r in ex]), 2),
              "| |past move|", round(spearman([abs(r['mom'] or 0)/r['scale'] for r in R], [abs(z(r,'realised')) for r in R]), 2))
        print("  signed IC (spearman pred vs real):  AI", round(spearman([z(r,'expected') for r in ex], [z(r,'realised') for r in ex]), 2),
              "| momentum", round(spearman([(r['mom'] or 0)/r['scale'] for r in R], [z(r,'realised') for r in R]), 2))

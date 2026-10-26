"""Statistical and fused tracks on the replays' moves, for the lab (run from the fi worktree):
- odds_all: every move, direction = the side of P(up); size 1.2σ when P(big) is in its top quarter, else 0.3σ.
- odds_sel: the same, called only when |P(up) − 0.5| ≥ T (else no call).
The P(big) cut is the dev calendar's 75th percentile (cal_rows.pkl), per horizon."""
import json, math, os, pickle, sys
from pathlib import Path
os.environ["MF_STATE"] = "out/lab/market.db"
sys.path[:0] = ["src", ".", "scripts"]
import forecast_desk
from measure import realised
from trial import lab, shadow

T = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1
here = Path(__file__).parent
S = realised.series(); m = shadow.model()
O = forecast_desk.odds_model(S)
cal = pickle.load(open(here / "cal_rows.pkl", "rb"))
cut = {}
for h in ("3d", "1w"):
    xs = sorted(r["pb"] for r in cal if r["h"] == h)
    cut[h] = xs[int(0.75 * len(xs))]
print("p_big cut", cut)
for replay in sys.argv[2:] or ("2026-07", "2026-08"):  # never the test month here
    if not Path(f"out/replay/{replay}/replay.json").exists():
        continue
    U = lab.moves(Path(f"out/replay/{replay}/state.db"))
    tracks = {"odds_all": {}, f"odds_sel{T}": {}, "fuse_all": {}, "fuse_claim": {}, "fuse_mom": {}, "fuse_mom_claim": {}}
    for r in U:
        got = O.of(r["factor"], r["origin"], r["horizon"])
        if not got:
            continue
        sg = 1 if got["p_up"] > 0.5 else -1
        size = 1.2 if got["p_big"] >= cut[r["horizon"]] else 0.3
        sc = m.factor(r["factor"]).vol_month * math.sqrt(m.horizons[r["horizon"]])
        k = "|".join(lab.key(r))
        tracks["odds_all"][k] = sg * size * sc
        tracks[f"odds_sel{T}"][k] = sg * size * sc if abs(got["p_up"] - 0.5) >= T else 0.0
        # fusion: the agents' side (their drafts' mean), the odds' size
        e = r.get("expected") or 0.0
        a = (e > 0) - (e < 0)
        tracks["fuse_all"][k] = a * size * sc
        tracks["fuse_claim"][k] = a * size * sc if r.get("claim") in ("up", "down") else 0.0
        # the agents' side, the size of the move over the same horizon before (big moves come in clusters)
        mom = abs(lab.momentum(r, S) or 0.0)
        tracks["fuse_mom"][k] = a * max(mom, 0.25 * sc)
        tracks["fuse_mom_claim"][k] = a * max(mom, 0.25 * sc) if r.get("claim") in ("up", "down") else 0.0
    for name, t in tracks.items():
        p = Path(f"out/lab/tracks/{name}/{replay}.json"); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(t))
        print(replay, name, len(t), "moves,", sum(1 for v in t.values() if v), "called")

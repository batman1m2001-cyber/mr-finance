"""Learned fusion (backlog D): ridge logistic P(up) and P(big) fitted on the July replay's moves, scored once on
August's. Inputs per move: the agents' expected z, the claim's side × its share, the drafts' count, the odds' P(up)
and P(big), the trailing move z and the 60-day majority. Rules fixed before looking at August: call when
|P(up) − 0.5| ≥ 0.1 (fuse_d_sel) or always (fuse_d_all); size 1.2σ when P(big) ≥ July's 75th percentile, else
0.3σ. Writes the tracks for August only; run from the fi worktree."""
import json, os, sys
from pathlib import Path
import numpy as np
os.environ["MF_STATE"] = "out/lab/market.db"
sys.path[:0] = ["src", ".", "scripts"]
import forecast_desk
from measure import realised
from trial import lab

S = realised.series(); O = forecast_desk.odds_model(S)


def rows(replay):
    out = []
    for r in lab.moves(Path(f"out/replay/{replay}/state.db")):
        got = O.of(r["factor"], r["origin"], r["horizon"])
        if not got:
            continue
        sc = r["scale"]; e = (r.get("expected") or 0.0) / sc
        cs = {"up": 1, "down": -1}.get(r.get("claim"), 0) * (r.get("claim_share") or 0)
        mom = (lab.momentum(r, S) or 0.0) / sc; maj = (lab.majority(r, S) or 0.0) / sc
        up = [e, cs, got["p_up"] - 0.5, mom, maj]
        big = [got["p_big"], abs(e), abs(mom), len(r.get("drafts") or [])]
        z = None if r.get("realised") is None else r["realised"] / sc
        out.append({"r": r, "up": up, "big": big, "z": z, "sc": sc})
    return out


def fit(X, y, lam=5.0):
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = np.column_stack([np.ones(len(X)), (X - mu) / sd]); w = np.zeros(Z.shape[1])
    R = lam * np.eye(Z.shape[1]); R[0, 0] = 0
    for _ in range(50):
        p = 1 / (1 + np.exp(-Z @ w))
        g = Z.T @ (p - y) + R @ w; H = Z.T @ (Z * (p * (1 - p))[:, None]) + R
        w -= np.linalg.solve(H, g)
    return lambda Q: 1 / (1 + np.exp(-np.column_stack([np.ones(len(Q)), (Q - mu) / sd]) @ w)), w


tracks = {"fuse_d_sel": {}, "fuse_d_all": {}}
for h in ("3d", "1w"):
    tr = [x for x in rows("2026-07") if x["r"]["horizon"] == h and x["z"] is not None]
    te = [x for x in rows("2026-08") if x["r"]["horizon"] == h]
    Xu = np.array([x["up"] for x in tr]); Xb = np.array([x["big"] for x in tr])
    pu, wu = fit(Xu, np.array([x["z"] > 0 for x in tr], float))
    pb, wb = fit(Xb, np.array([abs(x["z"]) >= 1 for x in tr], float))
    cut = np.quantile(pb(Xb), 0.75)
    print(h, "train", len(tr), "up w", np.round(wu, 2), "big w", np.round(wb, 2), "cut", round(cut, 3))
    qu = pu(np.array([x["up"] for x in te])); qb = pb(np.array([x["big"] for x in te]))
    for x, a, b in zip(te, qu, qb):
        k = "|".join(lab.key(x["r"])); v = (1 if a > 0.5 else -1) * (1.2 if b >= cut else 0.3) * x["sc"]
        tracks["fuse_d_all"][k] = v
        tracks["fuse_d_sel"][k] = v if abs(a - 0.5) >= 0.1 else 0.0
for name, t in tracks.items():
    p = Path(f"out/lab/tracks/{name}/2026-08.json"); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(t)); print(name, len(t), "moves,", sum(1 for v in t.values() if v), "called")
    Path(f"out/lab/tracks/{name}/2026-07.json").write_text("{}")  # in-sample month: no calls, never scored

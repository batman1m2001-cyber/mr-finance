"""Export the odds' training matrices (2020-04 .. 2026-06) and the dev calendar's (cal_rows.pkl) for the GBM test.
Run from the fi worktree with the app venv; the GBM itself runs in the scratch venv (gbm_eval.py)."""
import os, pickle, sys
from pathlib import Path
import numpy as np
os.environ["MF_STATE"] = "out/lab/market.db"
sys.path[:0] = ["src", "."]
from measure import realised
from trial import odds, shadow

S = realised.series(); m = shadow.model(); factors = sorted(S)
here = Path(__file__).parent
out = {}
for h in ("3d", "1w"):
    X, Xb, up, big, who = odds.training(S, m, h, "2020-04-01", "2026-06-30")
    out[f"{h}_X"] = X[:, :-1]; out[f"{h}_f"] = np.array([factors.index(w) for w in who])
    out[f"{h}_up"] = up; out[f"{h}_big"] = big
    rows = [r for r in pickle.load(open(here / "cal_rows.pkl", "rb")) if r["h"] == h]
    out[f"{h}_dX"] = np.array([odds.row(r, r["fid"], factors)[:-1] for r in rows])
    out[f"{h}_df"] = np.array([factors.index(r["fid"]) for r in rows])
    out[f"{h}_dz"] = np.array([r["z"] for r in rows]); out[f"{h}_dpu"] = np.array([r["pu"] for r in rows])
    out[f"{h}_dpb"] = np.array([r["pb"] for r in rows]); out[f"{h}_dd"] = np.array([r["d"] for r in rows])
np.savez(here / "gbm_data.npz", factors=np.array(factors), features=np.array(odds.FEATURES), **out)
print({k: v.shape for k, v in out.items()})

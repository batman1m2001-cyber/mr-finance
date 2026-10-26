import os, sys, pickle
os.environ["MF_STATE"] = "out/lab/market.db"; sys.path[:0] = ["src", "."]
from measure import realised
from trial import odds
S = realised.series()
O = odds.Odds(S)
pickle.dump({"w": O.w, "factors": O.factors, "base": O.base}, open("../improve/odds_w.pkl", "wb"))
names = list(odds.FEATURES) + O.factors
for h in O.w:
    for k in ("up", "big"):
        print(h, k, " ".join(f"{n}={v:+.2f}" for n, v in zip(names, O.w[h][k])))

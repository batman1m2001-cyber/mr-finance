"""LightGBM against the logistic odds on the dev calendar (trained 2020-04 .. 2026-06, the same features plus the
factor as a category). Direction: IC and accuracy of P(up); size: AUC of P(big). Settings fixed before looking."""
from pathlib import Path
import numpy as np
import lightgbm as lgb

D = np.load(Path(__file__).with_name("gbm_data.npz"))
factors = list(D["factors"])

def rank(a): return np.argsort(np.argsort(a))
def ic(a, b): return round(float(np.corrcoef(rank(a), rank(b))[0, 1]), 3)
def auc(s, y):
    r = rank(s) + 1; p = y.sum(); n = len(y) - p
    return round(float((r[y == 1].sum() - p * (p + 1) / 2) / (p * n)), 3)

P = dict(objective="binary", learning_rate=0.03, num_leaves=8, min_data_in_leaf=200, feature_fraction=0.8,
         bagging_fraction=0.8, bagging_freq=1, lambda_l2=10.0, verbose=-1, seed=7)
for h in ("3d", "1w"):
    X = np.column_stack([D[f"{h}_X"], D[f"{h}_f"]]); dX = np.column_stack([D[f"{h}_dX"], D[f"{h}_df"]])
    z = D[f"{h}_dz"]; big = (np.abs(z) >= 1).astype(int)
    cat = [X.shape[1] - 1]
    gu = lgb.train(P, lgb.Dataset(X, D[f"{h}_up"], categorical_feature=cat), num_boost_round=300)
    gb = lgb.train(P, lgb.Dataset(X, D[f"{h}_big"], categorical_feature=cat), num_boost_round=300)
    pu, pb = gu.predict(dX), gb.predict(dX)
    print(f"{h}: n={len(z)}  train n={len(X)}")
    print(f"  P(up)  IC  logistic {ic(D[f'{h}_dpu'], z)}  gbm {ic(pu, z)}   acc logistic "
          f"{np.mean((D[f'{h}_dpu'] > .5) == (z > 0)):.3f}  gbm {np.mean((pu > .5) == (z > 0)):.3f}")
    print(f"  P(big) AUC logistic {auc(D[f'{h}_dpb'], big)}  gbm {auc(pb, big)}")
    for i, f in enumerate(factors):
        k = D[f"{h}_df"] == i
        if k.sum():
            print(f"    {f:13} IC log {ic(D[f'{h}_dpu'][k], z[k]):6}  gbm {ic(pu[k], z[k]):6}   AUC big log "
                  f"{auc(D[f'{h}_dpb'][k], big[k]) if 0 < big[k].sum() < k.sum() else '-':>5}  gbm "
                  f"{auc(pb[k], big[k]) if 0 < big[k].sum() < k.sum() else '-':>5}")

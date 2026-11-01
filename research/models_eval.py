"""Hoe goed voorspellen de modellen, vergeleken met de markt? (out-of-sample, walk-forward)"""
import numpy as np
import pandas as pd

from sbagent.features import prepared
from sbagent.ml import feature_sets, logloss, rps, walk_forward

df = prepared(rich=True)
y = df.ftr.map({"A": 0, "D": 1, "H": 2}).values  # sklearn sorteert klassen: A, D, H
order = ["a", "d", "h"]
mask = df.season >= "1819"
res = {}
P = {}
P["Pinnacle open (devig)"] = df[[f"ref_{s}" for s in order]].values
P["Pinnacle slot (devig)"] = df[[f"refc_{s}" for s in order]].values
P["Marktgemiddelde (devig)"] = df[[f"fcons_{s}" for s in order]].values
P["Poisson online (v1)"] = df[[f"m_{s}" for s in order]].values
P["Dixon-Coles goals"] = df[[f"dc_{s}" for s in order]].values
P["Dixon-Coles schoten"] = df[[f"dcs_{s}" for s in order]].values
fs = feature_sets(df)
for name, kind in [("models", "lr"), ("market", "lr"), ("market+models", "lr"),
                   ("market+models+team", "lr"), ("market+models+team", "gbm"),
                   ("models+team", "lr"), ("models+team", "gbm")]:
    P[f"ML {kind}: {name}"] = walk_forward(df, fs[name], y, kind)
np.save("data/cache/ml_preds.npy", {k: v for k, v in P.items()}, allow_pickle=True)
rows = []
ok_all = mask.values & np.all([np.isfinite(p).all(1) for p in P.values()], axis=0)
for k, p in P.items():
    rows.append({"model": k, "logloss": round(logloss(p[ok_all], y[ok_all]), 5),
                 "RPS": round(rps(p[ok_all], y[ok_all]), 5)})
print("n =", ok_all.sum())
print(pd.DataFrame(rows).to_markdown(index=False))
# per seizoen: verschil ML-best vs Pinnacle
best = "ML lr: market+models+team"
per = []
for s in sorted(df.season[mask].unique()):
    m = ok_all & (df.season == s).values
    per.append({"season": s, "pinnacle": round(logloss(P["Pinnacle open (devig)"][m], y[m]), 4),
                "ml_lr_all": round(logloss(P[best][m], y[m]), 4),
                "ml_gbm_all": round(logloss(P["ML gbm: market+models+team"][m], y[m]), 4),
                "dc_shots": round(logloss(P["Dixon-Coles schoten"][m], y[m]), 4)})
print(pd.DataFrame(per).to_markdown(index=False))

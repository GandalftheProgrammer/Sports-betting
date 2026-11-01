"""Evaluatie van het 'voorspel de slotkoers'-model."""
import numpy as np
import pandas as pd

from sbagent.features import _cached, prepared
from sbagent.ml import logloss
from sbagent.movement import predict_close

df = prepared(rich=True)
for kind in ("ridge", "gbm"):
    mv = _cached(f"movement_{kind}", lambda d: predict_close(d, kind), df)
    m = (df.season >= "1819").values & df.ps_h.notna().values & df.psc_h.notna().values
    print(f"== {kind}")
    for s in "hdaou":
        act = (np.log(df[f"refc_{s}"] / (1 - df[f"refc_{s}"])) - np.log(df[f"ref_{s}"] / (1 - df[f"ref_{s}"]))).values
        pr = mv[f"mvd_{s}"].values
        ok = m & np.isfinite(act) & np.isfinite(pr)
        c = np.corrcoef(pr[ok], act[ok])[0, 1]
        hit = np.mean(np.sign(pr[ok]) == np.sign(act[ok]))
        print(f"  {s}: corr={c:.4f} richting-goed={hit:.3f} n={ok.sum()}")
    y = df.ftr.map({"A": 0, "D": 1, "H": 2}).values
    P = {"open": df[["ref_a", "ref_d", "ref_h"]].values, "voorspeld slot": mv[["mv_a", "mv_d", "mv_h"]].values,
         "echt slot": df[["refc_a", "refc_d", "refc_h"]].values}
    ok = m & np.all([np.isfinite(p).all(1) for p in P.values()], axis=0)
    for split, ss in (("TRAIN-periode 1819-2223", ["1819", "1920", "2021", "2122", "2223"]), ("VALID 2324-2425", ["2324", "2425"]), ("TEST 2526", ["2526"])):
        k = ok & df.season.isin(ss).values
        print("  ", split, {n: round(logloss(p[k], y[k]), 5) for n, p in P.items()})

"""'Voorspel de slotkoers'-model.

De slotkoers van Pinnacle is de beste kansschatting die er is (beter dan
de vroege koers). Als we met informatie die bij de vroege koers al bekend
is kunnen voorspellen waar de koers naartoe beweegt, kunnen we vroeg
wedden tegen koersen die later zakken → positieve Closing Line Value.

Target: verschil in log-odds tussen slot en open, per uitkomst.
Model: walk-forward (train op eerdere seizoenen), Ridge of gradient boosting.
Output: voorspelde slot-kansen  mv_h, mv_d, mv_a  (en mv_o, mv_u).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .ml import _logit, feature_sets

EPS = 1e-6


def movement_features(df: pd.DataFrame) -> pd.DataFrame:
    fs = feature_sets(df)
    X = fs["market+models+team"].copy()
    # expliciete 'model wijkt af van markt' signalen
    for s in "hda":
        X[f"gap_dc_{s}"] = df[f"dc_{s}"] - df[f"ref_{s}"]
        X[f"gap_dcs_{s}"] = df[f"dcs_{s}"] - df[f"ref_{s}"]
        X[f"gap_m_{s}"] = df[f"m_{s}"] - df[f"ref_{s}"]
        X[f"gap_cons_{s}"] = df[f"fcons_{s}"] - df[f"ref_{s}"]
        X[f"gap_b365_{s}"] = 1 / df[f"b365_{s}"] - 1 / df[f"ps_{s}"]
        X[f"gap_max_{s}"] = 1 / df[f"max_{s}"] - 1 / df[f"ps_{s}"]
    X["gap_dc_o"] = df["dc_o"] - df["ref_o"]
    X["gap_dcs_o"] = df["dcs_o"] - df["ref_o"]
    X["gap_cons_o"] = df["fcons_o"] - df["ref_o"]
    X["mk_o"] = _logit(df["ref_o"])
    return X


def _make(kind):
    if kind == "ridge":
        return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=300.0))
    return HistGradientBoostingRegressor(max_iter=300, learning_rate=0.03, max_leaf_nodes=15,
                                         min_samples_leaf=300, l2_regularization=1.0, random_state=0)


def predict_close(df: pd.DataFrame, kind: str = "ridge", first_test: str = "1819") -> pd.DataFrame:
    X = movement_features(df).values
    out = pd.DataFrame(index=df.index)
    has = df.ps_h.notna() & df.psc_h.notna()  # alleen echte Pinnacle open->slot paren als target
    for sels, tag in ((("h", "d", "a"), "1x2"), (("o", "u"), "ou")):
        preds = {}
        for s in sels:
            y = (_logit(df[f"refc_{s}"]) - _logit(df[f"ref_{s}"])).values
            okrow = has.values & np.isfinite(y)
            p = np.full(len(df), np.nan)
            for season in sorted(df.season.unique()):
                if season < first_test:
                    continue
                tr = (df.season < season).values & okrow
                te = (df.season == season).values
                if tr.sum() < 1500:
                    continue
                m = _make(kind)
                m.fit(X[tr], y[tr])
                p[te] = m.predict(X[te])
            preds[s] = p
        # voorspelde slotkans = open-kans verschoven met voorspelde beweging, hernormaliseren
        raw = np.column_stack([1 / (1 + np.exp(-(_logit(df[f"ref_{s}"].values) + preds[s])))
                               for s in sels])
        raw = raw / raw.sum(axis=1, keepdims=True)
        for j, s in enumerate(sels):
            out[f"mv_{s}"] = raw[:, j]
            out[f"mvd_{s}"] = preds[s]
    return out

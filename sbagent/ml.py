"""Walk-forward machine learning bovenop markt + modellen.

Idee: de markt (Pinnacle) is al heel goed. We laten een model leren
waar de markt *systematisch* naast zit, met de marktkans als belangrijkste
input en de rest (ratings, schoten, vorm, motivatie, ...) als correcties.

Walk-forward: voor seizoen s wordt alleen getraind op seizoenen < s.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

EPS = 1e-6


def _logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def feature_sets(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Bouwt een aantal feature-sets, van 'alleen markt' tot 'alles'."""
    F = pd.DataFrame(index=df.index)
    for s in "hda":
        F[f"mk_{s}"] = np.log(df[f"ref_{s}"].clip(EPS))
    F["mk_over"] = 1 / df.ps_h + 1 / df.ps_d + 1 / df.ps_a
    # verschil tussen consensus en scherpe markt (wie wijkt af?)
    for s in "hda":
        F[f"disagree_{s}"] = df[f"fcons_{s}"] - df[f"ref_{s}"]
    M = pd.DataFrame(index=df.index)
    for s in "hda":
        M[f"dc_{s}"] = np.log(df[f"dc_{s}"].clip(EPS))
        M[f"dcs_{s}"] = np.log(df[f"dcs_{s}"].clip(EPS))
    M["dc_ld"] = np.log(df.dc_lh) - np.log(df.dc_la)
    M["dcs_ld"] = np.log(df.dcs_lh) - np.log(df.dcs_la)
    M["pi_egd"] = df.pi_egd
    M["elo"] = df.elo_diff / 400
    T = pd.DataFrame(index=df.index)
    for st in ("gf", "ga", "sf", "sa", "tf", "ta", "cf", "ca"):
        T[f"d_ewm_{st}"] = df[f"h_ewm_{st}"] - df[f"a_ewm_{st}"]
    for c in ("luck_f", "luck_a", "form3", "form5", "streak", "last_margin", "rest", "ppg",
              "gdpg", "pos", "gap_rel", "gap_eur", "dead", "promoted", "popular"):
        T[f"h_{c}"] = df[f"h_{c}"]
        T[f"a_{c}"] = df[f"a_{c}"]
    T["round"] = df["round"]
    T["remaining"] = df["remaining"]
    T["midweek"] = df.date.dt.dayofweek.isin([1, 2, 3]).astype(float)
    T["covid"] = ((df.date >= "2020-05-15") & (df.date <= "2021-06-30")).astype(float)
    L = pd.get_dummies(df.league, prefix="lg").astype(float)
    return {
        "market": F,
        "models": M,
        "market+models": pd.concat([F, M], axis=1),
        "market+models+team": pd.concat([F, M, T, L], axis=1),
        "models+team": pd.concat([M, T, L], axis=1),
    }


def _make(kind: str):
    if kind == "lr":
        return make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                             LogisticRegression(C=0.05, max_iter=2000))
    if kind == "gbm":
        return HistGradientBoostingClassifier(max_iter=250, learning_rate=0.03, max_leaf_nodes=15,
                                              min_samples_leaf=200, l2_regularization=1.0,
                                              random_state=0)
    raise ValueError(kind)


def walk_forward(df: pd.DataFrame, X: pd.DataFrame, y: np.ndarray, kind: str = "lr",
                 first_test: str = "1819", min_train_rows: int = 2000) -> np.ndarray:
    """Geeft out-of-sample kansen (n, k) terug; NaN voor seizoenen zonder voorspelling."""
    seasons = sorted(df.season.unique())
    classes = np.unique(y[~pd.isna(y)])
    out = np.full((len(df), len(classes)), np.nan)
    for s in seasons:
        if s < first_test:
            continue
        tr = (df.season < s).values & ~pd.isna(y)
        te = (df.season == s).values
        if tr.sum() < min_train_rows:
            continue
        m = _make(kind)
        m.fit(X.values[tr], y[tr])
        out[te] = m.predict_proba(X.values[te])
    return out


def logloss(p: np.ndarray, y_idx: np.ndarray) -> float:
    ok = np.isfinite(p).all(axis=1)
    return float(-np.mean(np.log(np.clip(p[ok, :][np.arange(ok.sum()), y_idx[ok]], EPS, 1))))


def rps(p: np.ndarray, y_idx: np.ndarray) -> float:
    """Ranked probability score (standaard in voetbalvoorspellen; lager = beter)."""
    ok = np.isfinite(p).all(axis=1)
    p = p[ok]
    o = np.zeros_like(p)
    o[np.arange(len(p)), y_idx[ok]] = 1
    cp, co = np.cumsum(p, axis=1)[:, :-1], np.cumsum(o, axis=1)[:, :-1]
    return float(np.mean(((cp - co) ** 2).sum(axis=1) / (p.shape[1] - 1)))

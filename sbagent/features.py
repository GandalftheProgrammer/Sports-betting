"""Afgeleide kolommen: eerlijke kansen per referentiebron, modellen en teamfeatures.

Referentiebronnen (kolomprefix -> bron):
  fair_*    Pinnacle (open snapshot)             fairc_*    Pinnacle slot
  fbfe_*    Betfair Exchange (open)              fbfec_*    Betfair Exchange slot
  fcons_*   marktgemiddelde (consensus)          fconsc_*   consensus slot
  ref_*     beste beschikbare 'scherpe' schatting: Pinnacle, anders Betfair,
            anders consensus (gecorrigeerd met 'power' devig)
  refc_*    idem voor de slotkoers
"""
from __future__ import annotations

from functools import lru_cache
import numpy as np
import pandas as pd

from .data import ROOT, load_all
from .devig import fair_probs
from .model import PoissonRatings

SEL_1X2 = ("h", "d", "a")
SEL_OU = ("o", "u")
SEL_AH = ("ahh", "aha")
CACHE = ROOT / "data" / "cache"


def _devig(df, src, dst, sels, method):
    cols = [f"{src}_{s}" for s in sels]
    if not all(c in df for c in cols):
        for s in sels:
            df[f"{dst}_{s}"] = np.nan
        return
    p = fair_probs(df[cols].values, method)
    for j, s in enumerate(sels):
        df[f"{dst}_{s}"] = p[:, j]


def add_fair(df: pd.DataFrame, method: str = "power") -> pd.DataFrame:
    df = df.copy()
    pairs = [("ps", "fair"), ("psc", "fairc"), ("bfe", "fbfe"), ("bfec", "fbfec"),
             ("avg", "fcons"), ("avgc", "fconsc")]
    for src, dst in pairs:
        for sels in (SEL_1X2, SEL_OU):
            _devig(df, src, dst, sels, method)
    # AH: 2-weg devig per bron
    for src, dst in (("ps", "fair"), ("psc", "fairc"), ("avg", "fcons")):
        _devig(df, src, dst, SEL_AH, method)
    for sels in (SEL_1X2, SEL_OU, SEL_AH):
        for s in sels:
            for open_close, (a, b, c) in (("ref", ("fair", "fbfe", "fcons")),
                                          ("refc", ("fairc", "fbfec", "fconsc"))):
                v = df[f"{a}_{s}"]
                if f"{b}_{s}" in df:
                    v = v.fillna(df[f"{b}_{s}"])
                if f"{c}_{s}" in df:
                    v = v.fillna(df[f"{c}_{s}"])
                df[f"{open_close}_{s}"] = v
    return df


def _cached(name: str, fn, df: pd.DataFrame) -> pd.DataFrame:
    import hashlib
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5("|".join(df.match_id).encode()).hexdigest()[:10]
    p = CACHE / f"{name}_{key}.pkl"
    if p.exists():
        return pd.read_pickle(p)
    c = fn(df)
    c.to_pickle(p)
    return c


@lru_cache(maxsize=2)
def prepared(method: str = "power", rich: bool = False) -> pd.DataFrame:
    """rich=True voegt teamfeatures en de sterkere ratingmodellen toe (trager, gecached)."""
    df = load_all()
    df = add_fair(df, method)
    df = df.join(PoissonRatings().run(df))
    if rich:
        from .ratings import DixonColes, Elo, PiRatings
        from .teamfeat import build
        df = df.join(_cached("teamfeat", build, df))
        df = df.join(_cached("dc_goals", lambda d: DixonColes(prefix="dc").run(d), df))
        df = df.join(_cached("dc_shots", lambda d: DixonColes(goal_weight=0.3, prefix="dcs").run(d), df))
        df = df.join(_cached("pi", lambda d: PiRatings().run(d), df))
        df = df.join(_cached("elo", lambda d: Elo().run(d), df))
        # 'voorspel de slotkoers'-modellen (ridge + gbm) en hun gemiddelde
        from .movement import predict_close
        for kind, pre in (("ridge", "mv"), ("gbm", "mg")):
            m = _cached(f"movement_{kind}", lambda d, k=kind: predict_close(d, k), df)
            df = df.join(m[[c for c in m if c.startswith("mv_")]].rename(
                columns=lambda c, p=pre: c.replace("mv_", f"{p}_")))
        for s in SEL_1X2 + SEL_OU:
            if f"mg_{s}" in df:
                df[f"avgmv_{s}"] = (df[f"mv_{s}"] + df[f"mg_{s}"]) / 2
    return df

"""Afgeleide kolommen: eerlijke kansen (Pinnacle devig) en model-kansen."""
from __future__ import annotations

from functools import lru_cache

import pandas as pd

from .data import load_all
from .devig import fair_probs
from .model import PoissonRatings

SEL_1X2 = ("h", "d", "a")
SEL_OU = ("o", "u")


def add_fair(df: pd.DataFrame, method: str = "power") -> pd.DataFrame:
    df = df.copy()
    for src, dst in (("ps", "fair"), ("psc", "fairc")):
        p = fair_probs(df[[f"{src}_{s}" for s in SEL_1X2]].values, method)
        for j, s in enumerate(SEL_1X2):
            df[f"{dst}_{s}"] = p[:, j]
        p = fair_probs(df[[f"{src}_{s}" for s in SEL_OU]].values, method)
        for j, s in enumerate(SEL_OU):
            df[f"{dst}_{s}"] = p[:, j]
    return df


@lru_cache(maxsize=4)
def prepared(method: str = "power") -> pd.DataFrame:
    df = load_all()
    df = add_fair(df, method)
    df = df.join(PoissonRatings().run(df))
    return df

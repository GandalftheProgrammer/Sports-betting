"""Experiment-runner: de 'leer-lus' van de agent.

Discipline om overfitting te voorkomen (de grootste valkuil bij backtesten):

    TRAIN  2016/17 - 2022/23  -> hier wordt gezocht en getuned (veel pogingen)
    VALID  2023/24 - 2024/25  -> alleen de top-kandidaten van TRAIN worden hier getoetst
    TEST   2025/26            -> 'eindexamen', pas als een strategie VALID doorstaat

Elke run wordt gelogd in results/experiments.jsonl zodat we bijhouden wat
wel/niet werkte en hoeveel pogingen er gedaan zijn (meer pogingen = hogere
lat, vanwege multiple testing).
"""
from __future__ import annotations

import itertools
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import strategies as S
from .backtest import Staking, metrics, simulate, staking_dict
from .data import ROOT

SPLITS = {
    "train": ["1617", "1718", "1819", "1920", "2021", "2122", "2223"],
    "valid": ["2324", "2425"],
    "test": ["2526"],
    "all": ["1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"],
}
LOG = ROOT / "results" / "experiments.jsonl"


def _git_rev() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "nogit"


def p_positive(ledger: pd.DataFrame, n_boot: int = 2000, seed: int = 0) -> float:
    """Bootstrap-kans dat het echte (vlakke) rendement > 0 is."""
    if len(ledger) < 20:
        return float("nan")
    r = np.where(ledger.won, ledger.odds - 1, -1.0)
    rng = np.random.default_rng(seed)
    means = rng.choice(r, size=(n_boot, len(r)), replace=True).mean(axis=1)
    return float((means > 0).mean())


def run(df: pd.DataFrame, strategy: str, params: dict, staking: Staking | None = None,
        split: str = "train", bankroll: float = 100.0, log: bool = True, tag: str = "") -> dict:
    staking = staking or Staking()
    sub = df[df.season.isin(SPLITS[split])]
    bets = S.make(strategy, **params).bets(sub)
    ledger = simulate(sub, bets, bankroll, staking)
    m = metrics(sub, ledger, bankroll)
    m["p_pos"] = round(p_positive(ledger), 3) if len(ledger) else float("nan")
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "git": _git_rev(), "tag": tag,
        "split": split, "strategy": strategy,
        "params": {k: list(v) if isinstance(v, tuple) else v for k, v in params.items()},
        "staking": staking_dict(staking), "metrics": m,
    }
    if log:
        LOG.parent.mkdir(exist_ok=True)
        with LOG.open("a") as f:
            f.write(json.dumps(rec, default=float) + "\n")
    rec["ledger"] = ledger
    return rec


def grid(space: dict):
    keys = list(space)
    for vals in itertools.product(*(space[k] for k in keys)):
        yield dict(zip(keys, vals))


def search(df: pd.DataFrame, strategy: str, space: dict, staking: Staking | None = None,
           min_bets: int = 150, top_k: int = 3, tag: str = "search") -> pd.DataFrame:
    """Zoek op TRAIN, toets top_k op VALID. Selectie op t-stat (robuuster dan winst)."""
    staking = staking or Staking(method="flat", pct=0.01, max_day_frac=1.0)
    rows = []
    for params in grid(space):
        r = run(df, strategy, params, staking, "train", tag=tag)
        m = r["metrics"]
        if m["n_bets"] >= min_bets:
            rows.append({"params": params, **{f"tr_{k}": v for k, v in m.items()}})
    res = pd.DataFrame(rows)
    if res.empty:
        return res
    res = res.sort_values("tr_t_stat", ascending=False).reset_index(drop=True)
    for i in range(min(top_k, len(res))):
        r = run(df, strategy, res.at[i, "params"], staking, "valid", tag=tag)
        for k, v in r["metrics"].items():
            res.loc[i, f"va_{k}"] = v
    res.attrs["n_trials"] = len(rows)
    return res


def leaderboard(split: str = "valid", n: int = 15) -> pd.DataFrame:
    if not LOG.exists():
        return pd.DataFrame()
    recs = [json.loads(l) for l in LOG.open()]
    rows = [{"strategy": r["strategy"], "params": json.dumps(r["params"]),
             "staking": r["staking"]["method"], **r["metrics"]}
            for r in recs if r["split"] == split]
    lb = pd.DataFrame(rows).drop_duplicates(subset=["strategy", "params", "staking"], keep="last")
    return lb.sort_values("t_stat", ascending=False).head(n)

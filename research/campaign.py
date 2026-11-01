"""Onderzoekscampagne #1: welke strategieën hebben historisch een echte edge?

Draai:  python -m research.campaign            (schrijft results/REPORT.md)
        python -m research.campaign --test     (ook het eindexamen op 2025/26)
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from sbagent import strategies as S
from sbagent.backtest import Staking, metrics, simulate
from sbagent.data import LEAGUES, ROOT
from sbagent.experiments import SPLITS, run, search
from sbagent.features import prepared

OUT = ROOT / "results"
FLAT = Staking(method="flat", pct=0.01, max_day_frac=1.0, min_stake=0)


def flat_eval(df, bets):
    """Rendement bij 1 eenheid op elke kandidaat (zonder bankroll-effecten)."""
    if len(bets) == 0:
        return dict(n=0, yield_=np.nan, t=np.nan)
    r = S.unit_return(df, bets)
    t = r.mean() / (r.std(ddof=1) / np.sqrt(len(r)))
    return dict(n=len(r), yield_=round(r.mean(), 4), t=round(t, 2))


def bias_tests(df):
    rows = []
    tests = {
        "Alles (Pinnacle)": dict(book="ps"),
        "Alles (Bet365)": dict(book="b365"),
        "Alles (gem. markt)": dict(book="avg"),
        "Grote favorieten <1.5 (Pinnacle)": dict(book="ps", max_odds=1.5),
        "Grote favorieten <1.5 (Bet365)": dict(book="b365", max_odds=1.5),
        "Longshots >7 (Pinnacle)": dict(book="ps", min_odds=7),
        "Longshots >7 (Bet365)": dict(book="b365", min_odds=7),
        "Thuis (Pinnacle)": dict(book="ps", sels=("h",)),
        "Gelijkspel (Pinnacle)": dict(book="ps", sels=("d",)),
        "Uit (Pinnacle)": dict(book="ps", sels=("a",)),
        "Over 2.5 (Pinnacle)": dict(book="ps", sels=("o",), markets=("ou",)),
        "Under 2.5 (Pinnacle)": dict(book="ps", sels=("u",), markets=("ou",)),
    }
    for name, p in tests.items():
        rows.append({"test": name, **flat_eval(df, S.make("odds_band", **p).bets(df))})
    # 'grote clubs' bias: uitploeg is topclub en favoriet
    for lg in LEAGUES:
        rows.append({"test": f"Alles {lg} (Pinnacle)",
                     **flat_eval(df, S.make("odds_band", book="ps", leagues=(lg,)).bets(df))})
    return pd.DataFrame(rows)


def per_season(df, ledger):
    s = df.loc[ledger.row, "season"].values
    g = pd.DataFrame({"s": s, "r": ledger.ret.values})
    return g.groupby("s").r.agg(["count", "mean"]).round(3)


def main(do_test=False):
    df = prepared()
    OUT.mkdir(exist_ok=True)
    md = ["# Onderzoeksrapport — campagne #1", "",
          f"Data: {len(df)} wedstrijden, {df.season.nunique()} seizoenen, competities: "
          + ", ".join(f"{k} ({v})" for k, v in LEAGUES.items()), "",
          "Splitsing: TRAIN 2016/17–2022/23 (zoeken) · VALID 2023/24–2024/25 (toetsen) · "
          "TEST 2025/26 (eindexamen).", ""]

    # 1. biases
    bt = bias_tests(df[df.season.isin(SPLITS["train"] + SPLITS["valid"])])
    md += ["## 1. Bekende marktbiases (vlakke inzet op alles in de groep, TRAIN+VALID)", "",
           "Een `yield` van −0,03 betekent 3% verlies per ingezette euro. `t` > 2 is pas "
           "statistisch interessant.", "", bt.to_markdown(index=False), ""]

    # 2. value vs sharp: zoeken
    space = {"book": ["b365", "soft", "max"], "min_edge": [0.0, 0.01, 0.02, 0.03, 0.05],
             "max_edge": [None, 0.15], "max_odds": [3.0, 6.0, 15.0], "min_odds": [1.3],
             "markets": [("1x2",), ("ou",), ("1x2", "ou")]}
    res = search(df, "value_vs_sharp", space, FLAT, min_bets=150, top_k=8, tag="c1_value")
    md += ["## 2. Value betting t.o.v. Pinnacle (zoeken op TRAIN, top-8 getoetst op VALID)", "",
           f"Aantal geteste combinaties: {res.attrs.get('n_trials')}", ""]
    cols = ["params", "tr_n_bets", "tr_flat_yield", "tr_clv", "tr_t_stat",
            "va_n_bets", "va_flat_yield", "va_clv", "va_t_stat", "va_p_pos"]
    show = res.head(8)[cols].copy()
    show["params"] = show.params.map(lambda p: json.dumps({k: v for k, v in p.items() if k != "min_odds"}))
    md += [show.to_markdown(index=False), ""]

    # per boek het beste, eerlijk vergelijk
    md += ["### Beste per boek (TRAIN-selectie)", ""]
    for book in ["b365", "soft", "max"]:
        sub = res[res.params.map(lambda p: p["book"] == book)]
        if sub.empty:
            continue
        p = sub.iloc[0].params
        rv = run(df, "value_vs_sharp", p, FLAT, "valid", tag="c1_bestbook")
        m = rv["metrics"]
        md.append(f"- **{book}** {json.dumps(p)} → VALID: {m['n_bets']} bets, yield "
                  f"{m['flat_yield']:+.3f}, CLV {m['clv']:+.3f}, t={m['t_stat']}, P(winst)={m['p_pos']}")
    md.append("")

    # 3. eigen model
    mspace = {"book": ["soft", "max"], "weight": [0.15, 0.3, 0.5, 1.0],
              "min_edge": [0.02, 0.04, 0.08], "max_odds": [5.0], "markets": [("1x2",), ("ou",)]}
    mres = search(df, "model_value", mspace, FLAT, min_bets=150, top_k=4, tag="c1_model")
    md += ["## 3. Eigen Poisson-model (gemengd met Pinnacle)", ""]
    if not mres.empty:
        show = mres.head(4)[[c for c in cols if c in mres]].copy()
        show["params"] = show.params.map(json.dumps)
        md += [show.to_markdown(index=False), ""]

    # 4. arbitrage
    arb = S.make("arbitrage", book="max", min_margin=0.0).bets(df)
    arb_m = arb.drop_duplicates(["row", "market"])
    cnt = arb_m.groupby(df.loc[arb_m.row, "season"].values).edge.agg(["count", "mean"]).round(4)
    md += ["## 4. Arbitrage (beste marktkoersen, alle seizoenen)", "",
           "Aantal 'surebets' per seizoen en gemiddelde gegarandeerde marge:", "",
           cnt.to_markdown(), ""]

    # 5. staking met 100 euro op de beste VALID-strategie
    best = res.dropna(subset=["va_t_stat"]).sort_values("va_t_stat", ascending=False)
    md += ["## 5. Staking-simulatie met €100 (VALID-periode, met limieten)", ""]
    if not best.empty:
        p = best.iloc[0].params
        md.append(f"Strategie: `value_vs_sharp` {json.dumps(p)}")
        md.append("")
        rows = []
        for name, st in {
            "vlak 1% start": Staking(method="flat", pct=0.01),
            "2% van bankroll": Staking(method="pct", pct=0.02),
            "Kelly 10%": Staking(method="kelly", kelly_frac=0.10),
            "Kelly 25%": Staking(method="kelly", kelly_frac=0.25),
            "Kelly 50%": Staking(method="kelly", kelly_frac=0.50, max_bet_frac=0.05),
        }.items():
            for split in ["valid"] + (["test"] if do_test else []):
                r = run(df, "value_vs_sharp", p, st, split, tag="c1_staking")
                m = r["metrics"]
                rows.append({"staking": name, "split": split, "bets": m["n_bets"],
                             "eind €": m["final"], "max drawdown": m["max_dd"],
                             "yield": m["yield"], "CLV": m["clv"]})
        md += [pd.DataFrame(rows).to_markdown(index=False), ""]
        led = run(df, "value_vs_sharp", p, FLAT, "all", log=False)["ledger"]
        md += ["Per seizoen (vlakke inzet, alle seizoenen — let op: TRAIN-seizoenen zijn "
               "in-sample):", "", per_season(df, led).to_markdown(), ""]

    (OUT / "REPORT.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    main(ap.parse_args().test)

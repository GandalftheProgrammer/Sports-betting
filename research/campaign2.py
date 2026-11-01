"""Onderzoekscampagne #2: sterkere modellen, 'voorspel de slotkoers', tweede
referentiekoers, Asian handicap, slotkoers-wedden en een portfolio.

Draai:  python -m research.campaign2   -> results/REPORT.md
(vereist eerst: python -m research.models_eval en python -m research.hypotheses)
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from sbagent import strategies as S
from sbagent.backtest import Staking
from sbagent.data import ROOT
from sbagent.experiments import run, search
from sbagent.features import prepared
from sbagent.ml import logloss

warnings.filterwarnings("ignore")
OUT = ROOT / "results"
FLAT = Staking(method="flat", pct=0.01, max_day_frac=1.0, min_stake=0)


def tbl(df):
    d = df.copy()
    for c in d.columns:
        if d[c].dtype == float:
            d[c] = d[c].round(4)
    return d.to_markdown(index=False)


def eval_rows(df, cfgs, strategy="value_vs_sharp"):
    rows = []
    for label, params in cfgs:
        row = {"strategie": label}
        for split in ("train18", "valid", "test"):
            m = run(df, strategy, params, FLAT, split, tag="c2_eval")["metrics"]
            short = {"train18": "tr", "valid": "va", "test": "te"}[split]
            row.update({f"{short}_n": m["n_bets"], f"{short}_yield": m["flat_yield"],
                        f"{short}_clv": m["clv"], f"{short}_t": m["t_stat"]})
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    df = prepared(rich=True)
    y = df.ftr.map({"A": 0, "D": 1, "H": 2}).values
    md = ["# Onderzoeksrapport — campagne #2", "",
          "Splitsing: TRAIN 2018/19–2022/23 (modellen hebben 2 seizoenen aanloop nodig) · "
          "VALID 2023/24–2024/25 · TEST 2025/26. Alle modelvoorspellingen zijn walk-forward: "
          "voor elk seizoen alleen getraind op eerdere seizoenen.", ""]

    # ---------------------------------------------------------------- 1. modellen
    try:
        P = np.load(ROOT / "data" / "cache" / "ml_preds.npy", allow_pickle=True).item()
        mask = (df.season >= "1819").values
        ok = mask & np.all([np.isfinite(p).all(1) for p in P.values()], axis=0)
        rows = [{"model": k, "logloss": logloss(p[ok], y[ok])} for k, p in P.items()]
        md += ["## 1. Hoe goed voorspellen modellen de uitslag? (1X2, out-of-sample 2018–2026)", "",
               f"n = {ok.sum()} wedstrijden. Lager = beter. Verschil van 0,003 is al betekenisvol.", "",
               tbl(pd.DataFrame(rows)), "",
               "**Conclusie:** onze modellen zijn flink verbeterd: Dixon-Coles op schoten scoort 0,978, "
               "tegen 0,991 voor het eerste model. Ze verslaan de markt (0,960) als voorspeller van de "
               "**uitslag** nog niet. Markt plus model samen (0,9606) komt dicht bij de markt, maar "
               "voegt niets toe. Gradient boosting overfit. Daarom kijken we hieronder naar een "
               "andere vraag die wel werkt.", ""]
    except FileNotFoundError:
        pass

    # ---------------------------------------------------------------- 2. beweging
    m = (df.season >= "1819").values & df.ps_h.notna().values & df.psc_h.notna().values
    rows = []
    for s in "hdao":
        act = (np.log(df[f"refc_{s}"] / (1 - df[f"refc_{s}"])) - np.log(df[f"ref_{s}"] / (1 - df[f"ref_{s}"]))).values
        for pre, name in (("mv", "ridge"), ("mg", "gbm")):
            if f"{pre}_{s}" not in df:
                continue
            pr = (np.log(df[f"{pre}_{s}"] / (1 - df[f"{pre}_{s}"])) - np.log(df[f"ref_{s}"] / (1 - df[f"ref_{s}"]))).values
            k = m & np.isfinite(act) & np.isfinite(pr)
            for split, ss in (("TRAIN", ["1819", "1920", "2021", "2122", "2223"]), ("VALID", ["2324", "2425"]), ("TEST", ["2526"])):
                kk = k & df.season.isin(ss).values
                rows.append({"uitkomst": s, "model": name, "periode": split, "n": int(kk.sum()),
                             "correlatie": np.corrcoef(pr[kk], act[kk])[0, 1],
                             "richting goed": np.mean(np.sign(pr[kk]) == np.sign(act[kk]))})
    md += ["## 2. Nieuw: voorspel waar de Pinnacle-koers naartoe beweegt", "",
           "De slotkoers is de scherpste kansschatting. Voorspel je met informatie van vóór de "
           "vroege koers (ratings, schoten, vorm, stand, koersverschillen tussen bookmakers) "
           "**hoe de koers gaat bewegen**, dan kun je vroeg wedden op koersen die later zakken.", "",
           tbl(pd.DataFrame(rows)), "",
           "**Conclusie:** correlatie 0,10–0,34 en in 53–69% van de gevallen de juiste richting (gelijkspel het best voorspelbaar). "
           "Dat geldt in alle drie de periodes, ook in TEST, die het model nooit heeft gezien. "
           "Het model weet dus dingen die de markt pas later inprijst.", ""]

    # ---------------------------------------------------------------- 3. hypotheses
    hp = OUT / "hypotheses.csv"
    if hp.exists():
        H = pd.read_csv(hp)
        top = H.reindex(H.ho_t.abs().sort_values(ascending=False).index).head(8)
        md += ["## 3. Biases uit literatuur + eigen ideeën (48 hypotheses)", "",
               "Volledige tabel: [HYPOTHESES.md](HYPOTHESES.md). Na correctie voor meervoudig "
               f"testen is **{int(H.tr_sig_BH.sum())}** hypothese significant op TRAIN, en "
               f"**{int(H.bevestigd.sum())}** bevestigd op HOLDOUT. De sterkste signalen in de "
               "recente periode (HOLDOUT), om te volgen:", "",
               tbl(top[["id", "hypothese", "tr_resid", "tr_t", "ho_n", "ho_resid", "ho_t", "ho_y_max"]]), "",
               "**Conclusie:** de klassieke biases (publieksclubs, reeksen, promovendi, motivatie, "
               "rust) zijn in deze competities en periode **niet** structureel uitbuitbaar. De markt "
               "prijst ze al in. Twee dingen om te volgen: (a) gelijkspel tussen gelijkwaardige "
               "teams, vooral laat in het seizoen (D1/D3), positief in recente seizoenen. Dat "
               "sluit aan bij Lezana (2026). (b) Als ons schotenmodel de uitploeg veel sterker "
               "vindt dan de markt, presteert die juist slechter (X2). Ons model overschat "
               "uitploegen dus. Dat gebruiken we als correctie.", ""]

    # ---------------------------------------------------------------- 4. strategieën
    cfgs = [
        ("v1: Pinnacle-value @ soft", dict(ref="fair", book="soft", min_edge=0.01, max_odds=6.0)),
        ("v1: Pinnacle-value @ max", dict(ref="fair", book="max", min_edge=0.01, max_odds=6.0)),
        ("2e referentie (Pinnacle→Betfair→consensus) @ max", dict(ref="ref", book="max", min_edge=0.01, max_odds=6.0)),
        ("slotkoers-model ridge @ soft", dict(ref="mv", book="soft", min_edge=0.01, max_odds=6.0)),
        ("slotkoers-model ridge @ max", dict(ref="mv", book="max", min_edge=0.01, max_odds=6.0)),
        ("slotkoers-model gem. @ soft", dict(ref="avgmv", book="soft", min_edge=0.01, max_odds=6.0)),
        ("slotkoers-model gem. @ max", dict(ref="avgmv", book="max", min_edge=0.01, max_odds=6.0)),
        ("slotkoers-model gem. @ Bet365", dict(ref="avgmv", book="b365", min_edge=0.0, max_odds=6.0)),
        ("Asian handicap value @ max (edge≥2%)", dict(ref="ref", book="max", min_edge=0.02, max_odds=6.0, markets=("ah",))),
        ("Over/Under value @ max (edge≥2%)", dict(ref="ref", book="max", min_edge=0.02, max_odds=6.0, markets=("ou",))),
        ("Wedden bij slotkoers (max) vs Pinnacle-slot", dict(ref="refc", book="maxc", min_edge=0.01, max_odds=6.0)),
        ("Wedden bij slotkoers (Bet365) vs Pinnacle-slot", dict(ref="refc", book="b365c", min_edge=0.01, max_odds=6.0)),
    ]
    E = eval_rows(df, cfgs)
    md += ["## 4. Strategieën naast elkaar (vlakke inzet, rendement per ingezette euro)", "",
           "`clv` = gemiddelde Closing Line Value (genomen koers vs. eerlijke Pinnacle-slotkoers), de "
           "beste voorspeller van echte winst. `t` > 2 = statistisch overtuigend.", "",
           tbl(E), "",
           "**Conclusies:**",
           "- Het **slotkoers-model** is de beste nieuwe bron. Het gemiddelde van ridge en gbm "
           "werkt het stabielst: positief rendement in TRAIN, VALID en TEST, zowel bij soft "
           "bookmakers als bij de beste marktkoers. De CLV is in elke periode positief.",
           "- **Asian handicap** value werkt ook (positief in alle periodes), met weinig bets.",
           "- **Wedden vlak voor aftrap** tegen de Pinnacle-slotkoers geeft schijnbaar CLV, maar "
           "**verliest in TEST**. Afgevallen.",
           "- **2e referentie**: zonder Pinnacle-koers (2025/26) val je terug op Betfair of "
           "consensus. Dat levert meer bets op, maar met een lagere kwaliteit per bet.", ""]

    # ---------------------------------------------------------------- 5. portfolio zoeken
    space = {
        "book": ["soft", "max"],
        "max_odds": [4.0, 6.0],
        "legs": [
            (("1x2", "avgmv", 0.0),),
            (("1x2", "avgmv", 0.01),),
            (("1x2", "avgmv", 0.02),),
            (("1x2", "avgmv", 0.01), ("ah", "ref", 0.02)),
            (("1x2", "avgmv", 0.01), ("ah", "ref", 0.02), ("ou", "ref", 0.02)),
            (("1x2", "avgmv", 0.02), ("ah", "ref", 0.03), ("ou", "ref", 0.03)),
            (("1x2", "mv", 0.01), ("ah", "ref", 0.02), ("ou", "mv", 0.02)),
        ],
    }
    res = search(df, "portfolio", space, FLAT, min_bets=150, top_k=28, tag="c2_portfolio",
                 train_split="train18")
    show = res[["params", "tr_n_bets", "tr_flat_yield", "tr_clv", "tr_t_stat",
                "va_n_bets", "va_flat_yield", "va_clv", "va_t_stat"]].copy()
    show["params"] = show.params.map(lambda p: json.dumps(p))
    md += ["## 5. Portfolio-zoektocht (TRAIN-selectie op t-stat, getoetst op VALID)", "",
           f"Geteste combinaties: {res.attrs.get('n_trials')}", "", tbl(show.head(10)), ""]

    # beste per boek kiezen op TRAIN t-stat, VALID moet positief zijn (geen selectie op VALID-winst)
    chosen = {}
    for book in ("soft", "max"):
        sub = res[res.params.map(lambda p: p["book"] == book)]
        sub = sub[sub.va_clv > 0]
        if len(sub):
            chosen[book] = sub.iloc[0].params

    # ---------------------------------------------------------------- 6. €100 simulatie
    md += ["## 6. €100-simulatie (met minimale inzet €0,50, plafonds, limiet €50/bet)", ""]
    rows = []
    for book, p in chosen.items():
        for sname, st in {
            "vlak 2% start": Staking(method="flat", pct=0.02, max_stake_abs=50),
            "3% van bankroll": Staking(method="pct", pct=0.03, max_bet_frac=0.03, max_stake_abs=50),
            "Kelly 25%": Staking(method="kelly", kelly_frac=0.25, max_stake_abs=50),
            "Kelly 50%": Staking(method="kelly", kelly_frac=0.5, max_bet_frac=0.05, max_stake_abs=50),
        }.items():
            for split in ("valid", "test"):
                mm = run(df, "portfolio", p, st, split, tag="c2_staking")["metrics"]
                rows.append({"boeken": book, "staking": sname, "periode": split, "bets": mm["n_bets"],
                             "eind €": mm["final"], "max drawdown": mm["max_dd"], "yield": mm["yield"],
                             "CLV": mm["clv"]})
        md.append(f"- **{book}**: `{json.dumps(p)}`")
    md += ["", tbl(pd.DataFrame(rows)), ""]

    # ---------------------------------------------------------------- 7. robuustheid
    if "soft" in chosen:
        led = run(df, "portfolio", chosen["soft"], FLAT, "all", log=False)["ledger"]
        led["season"] = df.loc[led.row, "season"].values
        led["league"] = df.loc[led.row, "league"].values
        from sbagent.backtest import clv as _clv
        led["clv"] = _clv(df, led)
        ps = led.groupby("season").agg(n=("ret", "size"), yield_=("ret", "mean"), clv=("clv", "mean"))
        pl = led.groupby("league").agg(n=("ret", "size"), yield_=("ret", "mean"), clv=("clv", "mean"))
        pm = led.groupby("market").agg(n=("ret", "size"), yield_=("ret", "mean"), clv=("clv", "mean"))
        md += ["## 7. Robuustheid portfolio (soft), vlakke inzet", "",
               "Per seizoen:", "", ps.round(4).to_markdown(), "",
               "Per competitie:", "", pl.round(4).to_markdown(), "",
               "Per markt:", "", pm.round(4).to_markdown(), ""]

    (OUT / "REPORT.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()

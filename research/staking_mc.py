"""Monte-Carlo: hoeveel % van de pot per bet? (proportioneel/progressief wedden)

Odds en edges komen uit de out-of-sample bets van het portfolio (2018-2026).
Scenario 'realistisch': echte winkans = (1 + CLV-edge) / odds  (CLV als ware edge)
Scenario 'backtest'  : de werkelijk behaalde rendementen (bootstrap; bevat geluk)
Bets worden per speelronde (5 tegelijk) geplaatst: inzet = % van pot bij begin ronde.
"""
import os

import numpy as np
import pandas as pd

from sbagent import strategies as S
from sbagent.backtest import Staking, clv, simulate
from sbagent.data import CORE_LEAGUES, ROOT
from sbagent.features import prepared

df = prepared(rich=True)
SEAS = ["1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]
P = dict(book="soft", max_odds=4.0, legs=(("1x2", "avgmv", 0.01), ("ou", "ref", 0.02), ("ah", "ref", 0.02)))
SCOPE = os.environ.get("SCOPE", "alle15")  # 'kern7' of 'alle15'
sub = df[df.season.isin(SEAS)]
if SCOPE == "kern7":
    sub = sub[sub.league.isin(CORE_LEAGUES)]
L = simulate(sub, S.make("portfolio", **P).bets(sub), 100, Staking(method="flat", pct=0.01, max_day_frac=1, min_stake=0))
L["clv"] = clv(sub, L)
odds = L.odds.values
ret = L.ret.values
edge_clv = np.nan_to_num(L.clv.values, nan=np.nanmean(L.clv))
edge_ex = L.edge.values  # wat het model VOORAF denkt (dit is wat je in het echt hebt)
SHRINK = np.mean(edge_clv) / np.mean(edge_ex)  # vooraf-edge overschat de echte edge
print(f"vooraf-edge gem={edge_ex.mean():.4f}, CLV gem={edge_clv.mean():.4f} -> krimpfactor {SHRINK:.2f}")
print(f"bets={len(L)} gem.odds={odds.mean():.2f} gem.CLV={edge_clv.mean():.4f} backtest-yield={ret.mean():.4f}")
print(f"Kelly-fractie bij gem. edge {edge_clv.mean():.3f} en odds {odds.mean():.2f}: {edge_clv.mean()/(odds.mean()-1):.4f}")

rng = np.random.default_rng(1)
N_SIM = 4000
BETS_SEASON = int(round(len(L) / len(SEAS)))
PER_ROUND = max(5, BETS_SEASON // 38)


def sim(frac, seasons, scenario, kelly=None, edge_scale=1.0):
    n = BETS_SEASON * seasons
    idx = rng.integers(0, len(L), size=(N_SIM, n))
    o = odds[idx]
    if scenario == "realistisch":
        e = edge_clv[idx] * edge_scale
        p = np.clip((1 + e) / o, 0.01, 0.99)
        win = rng.random((N_SIM, n)) < p
        r = np.where(win, o - 1, -1.0)
    else:
        r = ret[idx]
    bank = np.full(N_SIM, 100.0)
    low = bank.copy()
    for k in range(0, n, PER_ROUND):
        sl = slice(k, k + PER_ROUND)
        if kelly is not None:
            ee = edge_ex[idx[:, sl]] * SHRINK  # inzet op basis van vooraf-edge, gekrompen
            f = np.clip(kelly * np.maximum(ee, 0) / (o[:, sl] - 1), 0, 0.05)
        else:
            f = np.full((N_SIM, r[:, sl].shape[1]), frac)
        stake = f * bank[:, None]
        tot = stake.sum(axis=1, keepdims=True)
        cap = 0.30 * bank[:, None]               # max 30% van de pot tegelijk in het spel
        stake = np.where(tot > cap, stake * cap / np.maximum(tot, 1e-9), stake)
        stake = np.where(stake < 0.5, 0, stake)        # minimale inzet €0,50
        bank = bank + (stake * r[:, sl]).sum(axis=1)
        low = np.minimum(low, bank)
    return bank, low


rows = []
for scen in ("realistisch", "backtest"):
    for seasons in (1, 3):
        for label, frac, kelly in [("1%", .01, None), ("2%", .02, None), ("3%", .03, None), ("5%", .05, None),
                                   ("8%", .08, None), ("12%", .12, None), ("Kelly ½", None, .5), ("Kelly 1×", None, 1.0)]:
            b, low = sim(frac, seasons, scen, kelly)
            rows.append({"scenario": scen, "seizoenen": seasons, "inzet/bet": label,
                         "mediaan €": np.median(b), "slechtste 10% €": np.percentile(b, 10),
                         "beste 10% €": np.percentile(b, 90), "kans op winst": (b > 100).mean(),
                         "kans pot ooit <€50": (low < 50).mean(), "kans pot <€20 (bijna op)": (low < 20).mean()})
R = pd.DataFrame(rows)
for c in R.columns[3:]:
    R[c] = R[c].round(3 if "kans" in c else 0)
md = [f"# Inzetstrategie: Monte-Carlo (4000 gesimuleerde verlopen) — {SCOPE}", "",
      f"Basis: {len(L)} out-of-sample portfolio-bets 2018–2026 (soft-mandje), gem. odds {odds.mean():.2f}, "
      f"gem. CLV {edge_clv.mean():+.2%}, backtest-rendement {ret.mean():+.2%}. Kelly gebruikt de edge die het model "
      f"VOORAF schat (gem. {edge_ex.mean():+.2%}), gekrompen met factor {SHRINK:.2f} naar het CLV-niveau. {BETS_SEASON} bets per seizoen, "
      f"{PER_ROUND} tegelijk per speelronde, inzet = % van de **actuele** pot (progressief), minimaal €0,50, "
      "max 30% van de pot tegelijk in het spel.", "",
      R.to_markdown(index=False)]
(ROOT / "results" / f"STAKING_{SCOPE}.md").write_text("\n".join(md))
print("\n".join(md))

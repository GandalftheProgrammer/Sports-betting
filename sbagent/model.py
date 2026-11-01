"""Eigen voorspelmodel: online Poisson-ratings (aanval/verdediging per team).

Werkt strikt chronologisch: de voorspelling voor wedstrijd t gebruikt alleen
uitslagen van vóór t (geen 'look-ahead'). Na elke speeldag worden de ratings
bijgewerkt met één gradiëntstap op de Poisson log-likelihood.

lambda_home = exp(mu + hfa + att[home] - def[away])
lambda_away = exp(mu +       att[away] - def[home])
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import poisson

MAXG = 10
_GOALS = np.arange(MAXG + 1)


def score_matrix(lh: float, la: float, rho: float = 0.0) -> np.ndarray:
    m = np.outer(poisson.pmf(_GOALS, lh), poisson.pmf(_GOALS, la))
    if rho:
        # Dixon-Coles correctie voor lage scores
        m[0, 0] *= 1 - lh * la * rho
        m[0, 1] *= 1 + lh * rho
        m[1, 0] *= 1 + la * rho
        m[1, 1] *= 1 - rho
        m /= m.sum()
    return m


def outcome_probs(lh: float, la: float, rho: float = 0.0):
    m = score_matrix(lh, la, rho)
    ph = np.tril(m, -1).sum()
    pd_ = np.trace(m)
    pa = np.triu(m, 1).sum()
    tot = np.add.outer(_GOALS, _GOALS)
    po = m[tot > 2.5].sum()
    return ph, pd_, pa, po


@dataclass
class PoissonRatings:
    lr: float = 0.06          # leersnelheid per wedstrijd
    season_shrink: float = 0.7  # ratings krimpen richting 0 bij nieuw seizoen
    promoted_rating: float = -0.15
    rho: float = -0.05

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Geeft per wedstrijd (in volgorde van df) model-kansen terug."""
        att: dict = {}
        dfn: dict = {}
        mu: dict = {}
        hfa: dict = {}
        cur_season: dict = {}
        out = np.full((len(df), 4), np.nan)
        lam = np.full((len(df), 2), np.nan)
        # groeperen per datum zodat wedstrijden op dezelfde dag elkaars info niet zien
        for _, idx in df.groupby("date", sort=True).indices.items():
            rows = df.iloc[idx]
            updates = []
            for i, r in zip(idx, rows.itertuples(index=False)):
                lg = r.league
                if cur_season.get(lg) != r.season:
                    if lg in cur_season:
                        for t in [k for k in att if k[0] == lg]:
                            att[t] *= self.season_shrink
                            dfn[t] *= self.season_shrink
                    cur_season[lg] = r.season
                mu.setdefault(lg, np.log(1.35))
                hfa.setdefault(lg, 0.25)
                h, a = (lg, r.home), (lg, r.away)
                for t in (h, a):
                    if t not in att:
                        att[t] = self.promoted_rating
                        dfn[t] = self.promoted_rating
                lh = np.exp(mu[lg] + hfa[lg] + att[h] - dfn[a])
                la = np.exp(mu[lg] + att[a] - dfn[h])
                out[i] = outcome_probs(lh, la, self.rho)
                lam[i] = (lh, la)
                updates.append((lg, h, a, lh, la, r.fthg, r.ftag))
            for lg, h, a, lh, la, gh, ga in updates:
                eh, ea = gh - lh, ga - la
                att[h] += self.lr * eh
                dfn[a] -= self.lr * eh
                att[a] += self.lr * ea
                dfn[h] -= self.lr * ea
                mu[lg] += self.lr * 0.05 * (eh + ea)
                hfa[lg] += self.lr * 0.05 * (eh - ea)
        return pd.DataFrame({
            "m_h": out[:, 0], "m_d": out[:, 1], "m_a": out[:, 2],
            "m_o": out[:, 3], "m_u": 1 - out[:, 3],
            "m_lh": lam[:, 0], "m_la": lam[:, 1],
        }, index=df.index)

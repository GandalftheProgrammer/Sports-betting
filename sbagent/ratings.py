"""Sterkere voorspelmodellen (allemaal walk-forward, geen look-ahead).

1. DixonColes   – Poisson MLE met tijdsverval (Dixon & Coles 1997), wekelijks
                  opnieuw gefit per competitie. Optioneel op 'xG-proxy' i.p.v.
                  doelpunten: target = w*goals + (1-w)*conv*schoten_op_doel
                  (schoten zijn minder toevallig dan goals; Wheatcroft 2020).
2. PiRatings    – Constantinou & Fenton (2013): aparte thuis/uit-rating,
                  update o.b.v. verschil tussen verwacht en echt doelsaldo.
3. Elo          – met doelsaldo-multiplier, als baseline.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .model import outcome_probs


# ---------------------------------------------------------------- Dixon-Coles
@dataclass
class DixonColes:
    xi: float = 0.0025          # tijdsverval per dag (halfwaardetijd ~ 280 dagen)
    window_days: int = 730
    refit_days: int = 7
    goal_weight: float = 1.0    # 1 = alleen goals, 0 = alleen schoten-op-doel-proxy
    rho: float = -0.06
    l2: float = 0.5             # regularisatie richting gemiddeld team (helpt bij promovendi)
    prefix: str = "dc"

    def _fit(self, hi, ai, yh, ya, w, n, x0):
        # params: att[n], dfn[n], home, mu
        def f(p):
            att, dfn, home, mu = p[:n], p[n:2 * n], p[2 * n], p[2 * n + 1]
            lh = np.exp(mu + home + att[hi] - dfn[ai])
            la = np.exp(mu + att[ai] - dfn[hi])
            ll = w * (yh * np.log(lh) - lh + ya * np.log(la) - la)
            obj = -ll.sum() + self.l2 * (att @ att + dfn @ dfn)
            gh = w * (yh - lh)
            ga = w * (ya - la)
            g_att = -(np.bincount(hi, gh, n) + np.bincount(ai, ga, n)) + 2 * self.l2 * att
            g_dfn = (np.bincount(ai, gh, n) + np.bincount(hi, ga, n)) + 2 * self.l2 * dfn
            g = np.concatenate([g_att, g_dfn, [-gh.sum(), -(gh.sum() + ga.sum())]])
            return obj, g
        res = minimize(f, x0, jac=True, method="L-BFGS-B")
        return res.x

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        out = np.full((len(df), 6), np.nan)
        for lg, g in df.groupby("league"):
            g = g.sort_values("date")
            dates = g.date.values
            # target: goals of mix met schoten-op-doel proxy
            th = g.st_hst.values.astype(float)
            ta = g.st_ast.values.astype(float)
            gh = g.fthg.values.astype(float)
            ga = g.ftag.values.astype(float)
            conv = np.nansum(gh + ga) / max(np.nansum(th + ta), 1)
            if self.goal_weight < 1:
                ph = np.where(np.isfinite(th), th * conv, gh)
                pa = np.where(np.isfinite(ta), ta * conv, ga)
                yh = self.goal_weight * gh + (1 - self.goal_weight) * ph
                ya = self.goal_weight * ga + (1 - self.goal_weight) * pa
            else:
                yh, ya = gh, ga
            teams = sorted(set(g.home) | set(g.away))
            tix = {t: i for i, t in enumerate(teams)}
            hi_all = g.home.map(tix).values
            ai_all = g.away.map(tix).values
            n = len(teams)
            x0 = np.concatenate([np.zeros(2 * n), [0.25, np.log(1.3)]])
            uniq = np.unique(dates)
            next_fit = uniq[0]
            params = None
            gi = np.arange(len(g))
            pos = df.index.get_indexer(g.index)
            for d in uniq:
                if d >= next_fit:
                    past = (dates < d) & (dates >= d - np.timedelta64(self.window_days, "D"))
                    if past.sum() >= 150:
                        age = (d - dates[past]).astype("timedelta64[D]").astype(float)
                        w = np.exp(-self.xi * age)
                        params = self._fit(hi_all[past], ai_all[past], yh[past], ya[past], w, n,
                                           params if params is not None else x0)
                    next_fit = d + np.timedelta64(self.refit_days, "D")
                if params is None:
                    continue
                att, dfn, home, mu = params[:n], params[n:2 * n], params[2 * n], params[2 * n + 1]
                for k in gi[dates == d]:
                    h, a = hi_all[k], ai_all[k]
                    lh = np.exp(mu + home + att[h] - dfn[a])
                    la = np.exp(mu + att[a] - dfn[h])
                    out[pos[k]] = (*outcome_probs(lh, la, self.rho), lh, la)
        p = self.prefix
        return pd.DataFrame(out, index=df.index,
                            columns=[f"{p}_h", f"{p}_d", f"{p}_a", f"{p}_o", f"{p}_lh", f"{p}_la"])


# ---------------------------------------------------------------- Pi-ratings
@dataclass
class PiRatings:
    lam: float = 0.06   # leersnelheid
    gam: float = 0.5    # kruis-leren thuis<->uit
    b: float = 10.0
    c: float = 3.0

    def _exp_gd(self, r):
        return np.sign(r) * (self.b ** (np.abs(r) / self.c) - 1)

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        R = {}
        diff = np.full(len(df), np.nan)
        egd = np.full(len(df), np.nan)
        for _, idx in df.groupby("date", sort=True).indices.items():
            rows = df.iloc[idx]
            ups = []
            for i, r in zip(idx, rows.itertuples(index=False)):
                h, a = (r.league, r.home), (r.league, r.away)
                rh = R.setdefault(h, [0.0, 0.0])  # [thuis, uit]
                ra = R.setdefault(a, [0.0, 0.0])
                e = self._exp_gd(rh[0]) - self._exp_gd(ra[1])
                diff[i] = rh[0] - ra[1]
                egd[i] = e
                ups.append((h, a, e, r.fthg - r.ftag))
            for h, a, e, gd in ups:
                err = abs(gd - e)
                psi = self.c * np.log10(1 + err)
                sh = psi if gd > e else -psi
                rh, ra = R[h], R[a]
                rh[0] += sh * self.lam
                rh[1] += sh * self.lam * self.gam
                ra[1] -= sh * self.lam
                ra[0] -= sh * self.lam * self.gam
        return pd.DataFrame({"pi_diff": diff, "pi_egd": egd}, index=df.index)


# ---------------------------------------------------------------- Elo
@dataclass
class Elo:
    k: float = 20.0
    hfa: float = 60.0
    carry: float = 0.8

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        E, season = {}, {}
        diff = np.full(len(df), np.nan)
        for _, idx in df.groupby("date", sort=True).indices.items():
            rows = df.iloc[idx]
            ups = []
            for i, r in zip(idx, rows.itertuples(index=False)):
                for t in ((r.league, r.home), (r.league, r.away)):
                    if t not in E:
                        E[t] = 1450.0
                    if season.get(t) not in (None, r.season):
                        E[t] = 1500 + self.carry * (E[t] - 1500)
                    season[t] = r.season
                h, a = (r.league, r.home), (r.league, r.away)
                d = E[h] + self.hfa - E[a]
                diff[i] = d
                ups.append((h, a, d, r.fthg - r.ftag))
            for h, a, d, gd in ups:
                exp = 1 / (1 + 10 ** (-d / 400))
                res = 1.0 if gd > 0 else (0.5 if gd == 0 else 0.0)
                mult = np.log(abs(gd) + 1) + 1 if gd else 1.0
                delta = self.k * mult * (res - exp)
                E[h] += delta
                E[a] -= delta
        return pd.DataFrame({"elo_diff": diff}, index=df.index)

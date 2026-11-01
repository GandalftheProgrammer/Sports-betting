"""Pre-match teamfeatures, strikt chronologisch berekend (geen look-ahead).

Per wedstrijd en per kant (h_ = thuisploeg, a_ = uitploeg):
  ewm_gf/ga      exponentieel gewogen doelpunten voor/tegen
  ewm_sf/sa      schoten voor/tegen,  ewm_tf/ta  schoten op doel voor/tegen
  ewm_cf/ca      corners voor/tegen
  luck_f/a       doelpunten minus 'verwacht' o.b.v. schoten op doel (geluk/pech)
  form3/form5    punten per wedstrijd laatste 3/5
  streak         + aantal opeenvolgende overwinningen / - verliespartijen
  last_margin    doelsaldo vorige wedstrijd
  rest           dagen sinds vorige competitiewedstrijd
  gp, ppg, gdpg  gespeeld, punten en doelsaldo per wedstrijd dit seizoen
  pos            positie in de stand vóór de wedstrijd
  gap_rel        punten boven de degradatiestreep (positie n-2)
  gap_eur        punten achter de nummer 4 (Europees voetbal)
  dead           niets meer te winnen/verliezen (wiskundig-ish, laatste fase)
  promoted       nieuw in deze competitie t.o.v. vorig seizoen
Algemeen: round (speelronde), remaining (resterende wedstrijden), popular_h/a.
"""
from __future__ import annotations

from collections import defaultdict, deque

import numpy as np
import pandas as pd

# 'publieksclubs' (veel supporters/wedgeld). Voor de sentiment-bias hypothese.
POPULAR = {
    "E0": {"Man United", "Liverpool", "Arsenal", "Chelsea", "Man City", "Tottenham"},
    "SP1": {"Real Madrid", "Barcelona", "Ath Madrid"},
    "I1": {"Juventus", "Milan", "Inter", "Napoli", "Roma"},
    "D1": {"Bayern Munich", "Dortmund"},
    "F1": {"Paris SG", "Marseille", "Lyon"},
    "P1": {"Benfica", "Porto", "Sp Lisbon"},
    "N1": {"Ajax", "PSV Eindhoven", "Feyenoord"},
}

HALF_LIFE = 6.0  # wedstrijden
ALPHA = 1 - 0.5 ** (1 / HALF_LIFE)

_STATS = ("gf", "ga", "sf", "sa", "tf", "ta", "cf", "ca")


class _Team:
    __slots__ = ("ewm", "pts", "last_date", "streak", "last_margin", "season", "s_pts", "s_gd", "s_gp")

    def __init__(self):
        self.ewm = {}
        self.pts = deque(maxlen=5)
        self.last_date = None
        self.streak = 0
        self.last_margin = 0
        self.season = None
        self.s_pts = self.s_gd = self.s_gp = 0


def build(df: pd.DataFrame) -> pd.DataFrame:
    teams: dict = defaultdict(_Team)
    league_conv: dict = {}           # doelpunten per schot op doel per competitie (ewm)
    league_means: dict = {}
    prev_members: dict = defaultdict(set)   # (league, season) -> teams
    n_teams = df.groupby(["league", "season"]).apply(
        lambda g: len(set(g.home) | set(g.away)), include_groups=False).to_dict()

    cols = []
    for side in ("h", "a"):
        cols += [f"{side}_ewm_{s}" for s in _STATS]
        cols += [f"{side}_{c}" for c in ("luck_f", "luck_a", "form3", "form5", "streak",
                                          "last_margin", "rest", "gp", "ppg", "gdpg", "pos",
                                          "gap_rel", "gap_eur", "dead", "promoted", "popular")]
    cols += ["round", "remaining"]
    out = np.full((len(df), len(cols)), np.nan)
    ci = {c: i for i, c in enumerate(cols)}

    seasons_by_league = defaultdict(list)
    for (lg, s) in sorted(n_teams):
        seasons_by_league[lg].append(s)
    for (lg, s), g in df.groupby(["league", "season"]):
        prev_members[(lg, s)] = set(g.home) | set(g.away)

    for _, idx in df.groupby("date", sort=True).indices.items():
        rows = df.iloc[idx]
        pending = []
        # stand per competitie (voor positie/gaps), alleen berekenen als nodig
        tables = {}
        for i, r in zip(idx, rows.itertuples(index=False)):
            lg, s = r.league, r.season
            nt = n_teams[(lg, s)]
            total_rounds = 2 * (nt - 1)
            if (lg, s) not in tables:
                tab = [(t.s_pts, t.s_gd, name) for (l2, name), t in teams.items()
                       if l2 == lg and t.season == s]
                tab.sort(reverse=True)
                tables[(lg, s)] = tab
            tab = tables[(lg, s)]
            pos_map = {name: k + 1 for k, (_, _, name) in enumerate(tab)}
            pts_sorted = [p for p, _, _ in tab]
            ls = seasons_by_league[lg]
            prev_s = ls[ls.index(s) - 1] if ls.index(s) > 0 else None
            for side, name in (("h", r.home), ("a", r.away)):
                t = teams[(lg, name)]
                if t.season != s:  # nieuw seizoen: seizoensstatistieken resetten
                    t.season = s
                    t.s_pts = t.s_gd = t.s_gp = 0
                    t.streak = 0
                for st in _STATS:
                    out[i, ci[f"{side}_ewm_{st}"]] = t.ewm.get(st, np.nan)
                conv = league_conv.get(lg, 0.33)
                if "gf" in t.ewm and "tf" in t.ewm:
                    out[i, ci[f"{side}_luck_f"]] = t.ewm["gf"] - conv * t.ewm["tf"]
                    out[i, ci[f"{side}_luck_a"]] = t.ewm["ga"] - conv * t.ewm["ta"]
                p = list(t.pts)
                if p:
                    out[i, ci[f"{side}_form5"]] = np.mean(p)
                    out[i, ci[f"{side}_form3"]] = np.mean(p[-3:])
                out[i, ci[f"{side}_streak"]] = t.streak
                out[i, ci[f"{side}_last_margin"]] = t.last_margin
                if t.last_date is not None:
                    out[i, ci[f"{side}_rest"]] = min((r.date - t.last_date).days, 30)
                out[i, ci[f"{side}_gp"]] = t.s_gp
                if t.s_gp:
                    out[i, ci[f"{side}_ppg"]] = t.s_pts / t.s_gp
                    out[i, ci[f"{side}_gdpg"]] = t.s_gd / t.s_gp
                if t.s_gp >= 3 and name in pos_map:
                    out[i, ci[f"{side}_pos"]] = pos_map[name]
                    rel_idx = nt - 3  # 0-based index van de eerste degradatieplek
                    if len(pts_sorted) > rel_idx:
                        out[i, ci[f"{side}_gap_rel"]] = t.s_pts - pts_sorted[rel_idx]
                    if len(pts_sorted) >= 4:
                        out[i, ci[f"{side}_gap_eur"]] = pts_sorted[3] - t.s_pts
                    rem = total_rounds - t.s_gp
                    gr = t.s_pts - pts_sorted[rel_idx] if len(pts_sorted) > rel_idx else 0
                    ge = pts_sorted[min(5, len(pts_sorted) - 1)] - t.s_pts
                    out[i, ci[f"{side}_dead"]] = float(rem <= 6 and gr > 3 * rem * 0.5 and ge > 3 * rem * 0.5)
                out[i, ci[f"{side}_promoted"]] = float(prev_s is not None and name not in prev_members[(lg, prev_s)])
                out[i, ci[f"{side}_popular"]] = float(name in POPULAR.get(lg, ()))
            hg = teams[(lg, r.home)].s_gp
            out[i, ci["round"]] = hg + 1
            out[i, ci["remaining"]] = total_rounds - hg
            pending.append(r)

        for r in pending:
            lg = r.league
            gh, ga = r.fthg, r.ftag
            sh, sa = getattr(r, "st_hs"), getattr(r, "st_as")
            th, ta = getattr(r, "st_hst"), getattr(r, "st_ast")
            chh, cha = getattr(r, "st_hc"), getattr(r, "st_ac")
            if np.isfinite(th) and np.isfinite(ta) and th + ta > 0:
                c0 = league_conv.get(lg, 0.33)
                league_conv[lg] = 0.995 * c0 + 0.005 * ((gh + ga) / (th + ta))
            for name, f in ((r.home, (gh, ga, sh, sa, th, ta, chh, cha)),
                            (r.away, (ga, gh, sa, sh, ta, th, cha, chh))):
                t = teams[(lg, name)]
                for st, v in zip(_STATS, f):
                    if v is None or not np.isfinite(v):
                        continue
                    t.ewm[st] = v if st not in t.ewm else (1 - ALPHA) * t.ewm[st] + ALPHA * v
                gf, gaa = f[0], f[1]
                pts = 3 if gf > gaa else (1 if gf == gaa else 0)
                t.pts.append(pts)
                if pts == 3:
                    t.streak = t.streak + 1 if t.streak > 0 else 1
                elif pts == 0:
                    t.streak = t.streak - 1 if t.streak < 0 else -1
                else:
                    t.streak = 0
                t.last_margin = gf - gaa
                t.last_date = r.date
                t.s_pts += pts
                t.s_gd += gf - gaa
                t.s_gp += 1
    return pd.DataFrame(out, columns=cols, index=df.index)

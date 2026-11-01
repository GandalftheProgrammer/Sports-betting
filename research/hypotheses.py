"""Brede hypothese-campagne: ~40 marktbiases uit literatuur + eigen ideeën.

Voor elke hypothese: een conditie op pre-match info + een selectie (op wie/wat
wedden). Toets:
  residu = uitkomst (0/1) - eerlijke kans (Pinnacle devig, open)
  -> > 0 betekent: de markt onderschat deze groep structureel.
Dit meet *mispricing* los van de bookmakermarge. Daarnaast het echte rendement
bij Pinnacle-, soft- en max-koersen.

Discipline: ontdekken op TRAIN (2016/17-2022/23), bevestigen op HOLDOUT
(2023/24-2025/26). Benjamini-Hochberg correctie voor het aantal geteste
hypotheses (anders vind je altijd 'iets' bij toeval).

Draai: python -m research.hypotheses  -> results/HYPOTHESES.md
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from sbagent.data import ROOT
from sbagent.features import prepared
from sbagent import strategies as S

TRAIN = ["1617", "1718", "1819", "1920", "2021", "2122", "2223"]
HOLD = ["2324", "2425", "2526"]


def H(df):
    """Geeft lijst (id, beschrijving, selectie, mask) terug. Selectie 'team_h' etc. via kolommen."""
    d = df
    pop_h, pop_a = d.h_popular == 1, d.a_popular == 1
    weekend = d.date.dt.dayofweek >= 5
    late = d.remaining <= 6
    even = (d.ref_h - d.ref_a).abs() < 0.10
    luck_h = d.h_luck_f - d.h_luck_a
    luck_a = d.a_luck_f - d.a_luck_a
    shots_h = d.h_ewm_tf - d.h_ewm_ta
    shots_a = d.a_ewm_tf - d.a_ewm_ta
    covid = (d.date >= "2020-05-15") & (d.date <= "2021-06-30")
    rest_diff = d.h_rest - d.a_rest
    motivated_h = (d.h_gap_rel.between(-3, 3)) & late
    motivated_a = (d.a_gap_rel.between(-3, 3)) & late
    out = [
        # --- sentiment / publieksclubs (Forrest & Simmons 2008; Franck et al. 2011)
        ("S1", "Tegen publieksclub (uit) → thuis", "h", pop_a & ~pop_h),
        ("S2", "Tegen publieksclub (thuis) → uit", "a", pop_h & ~pop_a),
        ("S3", "Tegen publieksclub uit, weekend → thuis", "h", pop_a & ~pop_h & weekend),
        ("S4", "Op publieksclub uit → uit", "a", pop_a & ~pop_h),
        ("S5", "Publieksclub-duel → gelijk", "d", pop_a & pop_h),
        # --- recency / overreactie
        ("R1", "Thuis op winstreeks ≥4 → uit", "a", d.h_streak >= 4),
        ("R2", "Uit op winstreeks ≥4 → thuis", "h", d.a_streak >= 4),
        ("R3", "Thuis op verliesreeks ≥3 → thuis", "h", d.h_streak <= -3),
        ("R4", "Uit op verliesreeks ≥3 → uit", "a", d.a_streak <= -3),
        ("R5", "Thuis vorige wedstrijd ≥3 verschil gewonnen → uit", "a", d.h_last_margin >= 3),
        ("R6", "Uit vorige wedstrijd ≥3 verschil verloren → uit", "a", d.a_last_margin <= -3),
        ("R7", "Thuis vorige wedstrijd ≥3 verschil verloren → thuis", "h", d.h_last_margin <= -3),
        # --- geluk vs. onderliggende prestaties (schoten; Wheatcroft 2020)
        ("L1", "Thuis 'gelukkig' (goals >> schoten) → uit", "a", luck_h >= 0.6),
        ("L2", "Uit 'gelukkig' → thuis", "h", luck_a >= 0.6),
        ("L3", "Thuis 'pech' (goals << schoten) → thuis", "h", luck_h <= -0.6),
        ("L4", "Uit 'pech' → uit", "a", luck_a <= -0.6),
        ("L5", "Thuis domineert schoten maar slechte vorm → thuis", "h", (shots_h - shots_a >= 2) & (d.h_form5 <= 1.2)),
        ("L6", "Uit domineert schoten maar slechte vorm → uit", "a", (shots_a - shots_h >= 2) & (d.a_form5 <= 1.2)),
        # --- promovendi / seizoensfase
        ("P1", "Promovendus thuis, eerste 8 rondes → thuis", "h", (d.h_promoted == 1) & (d["round"] <= 8)),
        ("P2", "Promovendus uit, eerste 8 rondes → uit", "a", (d.a_promoted == 1) & (d["round"] <= 8)),
        ("P3", "Tegen promovendus thuis, eerste 8 rondes → uit", "a", (d.h_promoted == 1) & (d["round"] <= 8)),
        ("P4", "Eerste 3 rondes → gelijk", "d", d["round"] <= 3),
        # --- motivatie einde seizoen (Goddard & Asimakopoulos 2004)
        ("M1", "Thuis degradatiestrijd vs uit 'niets meer te spelen' → thuis", "h", motivated_h & (d.a_dead == 1)),
        ("M2", "Uit degradatiestrijd vs thuis 'niets meer te spelen' → uit", "a", motivated_a & (d.h_dead == 1)),
        ("M3", "Beide 'niets meer te spelen' → over 2.5", "o", (d.h_dead == 1) & (d.a_dead == 1)),
        ("M4", "Thuis 'niets meer te spelen' → uit", "a", (d.h_dead == 1) & late),
        ("M5", "Laatste 5 rondes → gelijk", "d", d.remaining <= 5),
        # --- structureel: thuisvoordeel / ghost games (Fischer & Haucap 2021)
        ("C1", "Ghost games (corona) → uit", "a", covid),
        ("C2", "Ghost games eerste 2 maanden → uit", "a", (d.date >= "2020-05-15") & (d.date <= "2020-07-31")),
        ("C3", "Midweek → thuis", "h", d.date.dt.dayofweek.isin([1, 2, 3])),
        ("C4", "Thuis ≥3 dagen meer rust → thuis", "h", rest_diff >= 3),
        ("C5", "Uit ≥3 dagen meer rust → uit", "a", rest_diff <= -3),
        # --- gelijkspel-bias (Pope & Peel 1989; Lezana 2026)
        ("D1", "Gelijkwaardige teams → gelijk", "d", even),
        ("D2", "Gelijkwaardig + weinig goals verwacht → gelijk", "d", even & (d.ref_o < 0.47)),
        ("D3", "Gelijkwaardig laat in seizoen → gelijk", "d", even & late),
        ("D4", "Lage goalverwachting → under 2.5", "u", d.ref_o < 0.42),
        # --- koersstructuur
        ("O1", "Thuis-underdog (kans < 25%) → thuis", "h", d.ref_h < 0.25),
        ("O2", "Zware uit-favoriet (kans > 65%) → uit", "a", d.ref_a > 0.65),
        ("O3", "Zware thuisfavoriet (kans > 75%) → thuis", "h", d.ref_h > 0.75),
        ("O4", "Hoge Pinnacle-marge (onzekere wedstrijd) → gelijk", "d", (1 / d.ps_h + 1 / d.ps_d + 1 / d.ps_a) > 1.04),
        ("O5", "Top vs. onder (≥10 plekken) → onderste ploeg thuis", "h", d.h_pos - d.a_pos >= 10),
        ("O6", "Top vs. onder (≥10 plekken) → onderste ploeg uit", "a", d.a_pos - d.h_pos >= 10),
        # --- over/under op basis van onderliggende stats
        ("G1", "Veel schoten op doel beide → over", "o", (d.h_ewm_tf + d.a_ewm_tf + d.h_ewm_ta + d.a_ewm_ta) >= 20),
        ("G2", "Weinig schoten op doel beide → under", "u", (d.h_ewm_tf + d.a_ewm_tf + d.h_ewm_ta + d.a_ewm_ta) <= 15),
        ("G3", "DC-model verwacht veel meer goals dan markt → over", "o", d.dcs_o - d.ref_o >= 0.06),
        ("G4", "DC-model verwacht veel minder goals dan markt → under", "u", d.dcs_o - d.ref_o <= -0.06),
        # --- model vs. markt
        ("X1", "DC-schoten ziet thuis ≥8%-punt sterker → thuis", "h", d.dcs_h - d.ref_h >= 0.08),
        ("X2", "DC-schoten ziet uit ≥8%-punt sterker → uit", "a", d.dcs_a - d.ref_a >= 0.08),
        ("X3", "Consensus hoger dan Pinnacle op thuis → uit (volg Pinnacle)", "a", d.fcons_h - d.ref_h >= 0.02),
        ("X4", "Bet365 duidelijk hoger dan Pinnacle → die selectie (thuis)", "h", 1 / d.b365_h < 1 / d.ps_h - 0.015),
    ]
    return out


def evaluate(df, sel, mask):
    sub = df[mask.fillna(False)]
    if len(sub) == 0:
        return None
    fair = sub[f"ref_{sel}"].values
    fairc = sub[f"refc_{sel}"].values
    b = pd.DataFrame({"row": sub.index, "market": "x", "sel": sel})
    won = (S.unit_return(sub, b.assign(odds=2.0)) > 0).astype(float)
    ok = np.isfinite(fair)
    res = won[ok] - fair[ok]
    t = res.mean() / (res.std(ddof=1) / np.sqrt(ok.sum())) if ok.sum() > 2 else np.nan
    out = {"n": int(ok.sum()), "resid": res.mean(), "t": t, "p": 2 * stats.t.sf(abs(t), ok.sum() - 1),
           "resid_close": np.nanmean(won - fairc)}
    for book in ("ps", "soft", "max"):
        o = sub[f"{book}_{sel}"].values
        k = np.isfinite(o)
        r = np.where(won[k] > 0, o[k] - 1, -1.0)
        out[f"y_{book}"] = r.mean() if k.sum() else np.nan
    return out


def bh(p, q=0.10):
    p = np.asarray(p)
    order = np.argsort(p)
    thr = q * (np.arange(1, len(p) + 1)) / len(p)
    passed = p[order] <= thr
    k = np.max(np.where(passed)[0]) + 1 if passed.any() else 0
    sig = np.zeros(len(p), bool)
    sig[order[:k]] = True
    return sig


def main():
    df = prepared(rich=True)
    rows = []
    for hid, desc, sel, mask in H(df):
        tr = evaluate(df, sel, mask & df.season.isin(TRAIN))
        ho = evaluate(df, sel, mask & df.season.isin(HOLD))
        if tr is None:
            continue
        if ho is None:  # bv. corona-periode: geen holdout mogelijk
            ho = {k: np.nan for k in tr}
        rows.append({"id": hid, "hypothese": desc,
                     **{f"tr_{k}": v for k, v in tr.items()}, **{f"ho_{k}": v for k, v in ho.items()}})
    R = pd.DataFrame(rows)
    R["tr_sig_BH"] = bh(R.tr_p.values)
    R["bevestigd"] = R.tr_sig_BH & (np.sign(R.ho_resid) == np.sign(R.tr_resid)) & (R.ho_p < 0.10)
    show = R[["id", "hypothese", "tr_n", "tr_resid", "tr_t", "tr_y_ps", "tr_y_max", "tr_sig_BH",
              "ho_n", "ho_resid", "ho_t", "ho_y_ps", "ho_y_soft", "ho_y_max", "bevestigd"]].copy()
    for c in show.columns:
        if show[c].dtype == float:
            show[c] = show[c].round(3)
    md = ["# Hypothese-campagne", "",
          "`resid` = werkelijke frequentie − eerlijke kans (Pinnacle, open). Positief = markt "
          "onderschat deze groep. `t` = t-statistiek. `y_ps/soft/max` = rendement per ingezette "
          "euro bij Pinnacle-, soft- en beste marktkoers. `tr_sig_BH` = significant op TRAIN "
          "na Benjamini-Hochberg-correctie (q=0,10) voor het aantal geteste hypotheses. "
          "`bevestigd` = ook in HOLDOUT (2023/24–2025/26) dezelfde richting met p<0,10.", "",
          show.to_markdown(index=False), ""]
    (ROOT / "results" / "HYPOTHESES.md").write_text("\n".join(md))
    print("\n".join(md))
    R.to_csv(ROOT / "results" / "hypotheses.csv", index=False)


if __name__ == "__main__":
    main()

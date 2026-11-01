"""Historische data laden en normaliseren (football-data.co.uk formaat).

Elke wedstrijd wordt één rij met een vast schema, ongeacht het seizoen:

    date, league, season, home, away, fthg, ftag, ftr
    1X2 odds per bron, "open" = snapshot vrijdag/dinsdag vóór de wedstrijd,
    "c" = slotkoers (closing) vlak voor aftrap:
        ps_h ps_d ps_a      Pinnacle (scherpe bookmaker; benchmark voor 'eerlijke' kans)
        psc_h psc_d psc_a   Pinnacle closing
        b365_h ...          Bet365 (representatief voor een 'soft' bookmaker)
        max_h ...           beste koers in de markt (line shopping, optimistisch)
        avg_h ...           gemiddelde markt
    Over/Under 2.5:
        ps_o ps_u, psc_o psc_u, b365_o b365_u, max_o max_u, avg_o avg_u
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

LEAGUES = {
    "E0": "Premier League",
    "SP1": "La Liga",
    "I1": "Serie A",
    "D1": "Bundesliga",
    "F1": "Ligue 1",
    "P1": "Primeira Liga",
    "N1": "Eredivisie",
}
SEASONS = ["1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425", "2526"]

# Sommige bronbestanden gebruiken afwijkende teamnamen; we normaliseren naar
# de football-data.co.uk namen zodat ratings over seizoenen heen doorlopen.
ALIASES = {
    "Leeds United": "Leeds", "Manchester City": "Man City", "Manchester Utd": "Man United",
    "Newcastle United": "Newcastle", "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham", "West Ham United": "West Ham",
    "Alavés": "Alaves", "Athletic Club": "Ath Bilbao", "Atlético Madrid": "Ath Madrid",
    "Celta Vigo": "Celta", "Espanyol": "Espanol", "Rayo Vallecano": "Vallecano",
    "Real Betis": "Betis", "Real Sociedad": "Sociedad",
    "Hellas Verona": "Verona",
    "Eintracht Frankfurt": "Ein Frankfurt", "Gladbach": "M'gladbach",
    "Hamburger SV": "Hamburg", "Köln": "FC Koln", "Mainz 05": "Mainz",
    "Paris Saint-Germain": "Paris SG",
}

SOFT_BOOKS = ["B365", "BW", "IW", "WH", "VC", "LB", "BV", "BMGM"]

# bronkolom-kandidaten -> doelkolom (eerste die bestaat wint)
COLMAP = {
    "ps_h": ["PSH"], "ps_d": ["PSD"], "ps_a": ["PSA"],
    "psc_h": ["PSCH"], "psc_d": ["PSCD"], "psc_a": ["PSCA"],
    "b365_h": ["B365H"], "b365_d": ["B365D"], "b365_a": ["B365A"],
    "b365c_h": ["B365CH"], "b365c_d": ["B365CD"], "b365c_a": ["B365CA"],
    "max_h": ["MaxH", "BbMxH"], "max_d": ["MaxD", "BbMxD"], "max_a": ["MaxA", "BbMxA"],
    "avg_h": ["AvgH", "BbAvH"], "avg_d": ["AvgD", "BbAvD"], "avg_a": ["AvgA", "BbAvA"],
    "maxc_h": ["MaxCH"], "maxc_d": ["MaxCD"], "maxc_a": ["MaxCA"],
    "ps_o": ["P>2.5"], "ps_u": ["P<2.5"],
    "psc_o": ["PC>2.5"], "psc_u": ["PC<2.5"],
    "b365_o": ["B365>2.5"], "b365_u": ["B365<2.5"],
    "max_o": ["Max>2.5", "BbMx>2.5"], "max_u": ["Max<2.5", "BbMx<2.5"],
    "avg_o": ["Avg>2.5", "BbAv>2.5"], "avg_u": ["Avg<2.5", "BbAv<2.5"],
    # slotkoersen overige bronnen (vanaf 2019/20)
    "avgc_h": ["AvgCH"], "avgc_d": ["AvgCD"], "avgc_a": ["AvgCA"],
    "b365c_o": ["B365C>2.5"], "b365c_u": ["B365C<2.5"],
    "maxc_o": ["MaxC>2.5"], "maxc_u": ["MaxC<2.5"],
    "avgc_o": ["AvgC>2.5"], "avgc_u": ["AvgC<2.5"],
    # Betfair Exchange (vanaf 2024/25) - koersen exclusief commissie
    "bfe_h": ["BFEH"], "bfe_d": ["BFED"], "bfe_a": ["BFEA"],
    "bfec_h": ["BFECH"], "bfec_d": ["BFECD"], "bfec_a": ["BFECA"],
    "bfe_o": ["BFE>2.5"], "bfe_u": ["BFE<2.5"],
}

# Asian handicap: lijn is t.o.v. de thuisploeg (bv -0.5 = thuis geeft half doelpunt)
AHMAP = {
    "ah_line": ["AHh", "BbAHh"],
    "ps_ahh": ["PAHH"], "ps_aha": ["PAHA"],
    "b365_ahh": ["B365AHH"], "b365_aha": ["B365AHA"],
    "max_ahh": ["MaxAHH", "BbMxAHH"], "max_aha": ["MaxAHA", "BbMxAHA"],
    "avg_ahh": ["AvgAHH", "BbAvAHH"], "avg_aha": ["AvgAHA", "BbAvAHA"],
    "ahc_line": ["AHCh"],
    "psc_ahh": ["PCAHH"], "psc_aha": ["PCAHA"],
    "maxc_ahh": ["MaxCAHH"], "maxc_aha": ["MaxCAHA"],
    "b365c_ahh": ["B365CAHH"], "b365c_aha": ["B365CAHA"],
}

# wedstrijdstatistieken (achteraf bekend; alleen gebruiken voor features van LATERE wedstrijden)
STATMAP = {
    "st_hs": "HS", "st_as": "AS", "st_hst": "HST", "st_ast": "AST",
    "st_hc": "HC", "st_ac": "AC", "st_hf": "HF", "st_af": "AF",
    "st_hy": "HY", "st_ay": "AY", "st_hr": "HR", "st_ar": "AR",
    "st_hthg": "HTHG", "st_htag": "HTAG",
}


def _read_csv(path: Path) -> pd.DataFrame:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"kan {path} niet lezen")


def load_file(path: Path, league: str, season: str) -> pd.DataFrame:
    raw = _read_csv(path)
    raw = raw.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])
    out = pd.DataFrame({
        "date": pd.to_datetime(raw["Date"], dayfirst=True, format="mixed"),
        "league": league,
        "season": season,
        "home": raw["HomeTeam"].str.strip().replace(ALIASES),
        "away": raw["AwayTeam"].str.strip().replace(ALIASES),
        "fthg": raw["FTHG"].astype(int),
        "ftag": raw["FTAG"].astype(int),
    })
    out["ftr"] = np.select([out.fthg > out.ftag, out.fthg == out.ftag], ["H", "D"], "A")
    for target, sources in {**COLMAP, **AHMAP}.items():
        col = next((s for s in sources if s in raw.columns), None)
        out[target] = pd.to_numeric(raw[col], errors="coerce").values if col else np.nan
    for target, col in STATMAP.items():
        out[target] = pd.to_numeric(raw[col], errors="coerce").values if col in raw.columns else np.nan
    if "Referee" in raw.columns:
        out["referee"] = raw["Referee"].values
    # 'soft' = beste koers over een mandje gangbare (niet-scherpe) bookmakers.
    # Realistischer dan 'max' (dat ook exchanges/obscure boeken bevat).
    for s in ("H", "D", "A"):
        cols = [f"{b}{s}" for b in SOFT_BOOKS if f"{b}{s}" in raw.columns]
        vals = raw[cols].apply(pd.to_numeric, errors="coerce") if cols else None
        out[f"soft_{s.lower()}"] = vals.max(axis=1).values if cols else np.nan
    out["soft_o"] = out["b365_o"]
    out["soft_u"] = out["b365_u"]
    out["soft_ahh"] = pd.to_numeric(raw["B365AHH"], errors="coerce").values if "B365AHH" in raw else np.nan
    out["soft_aha"] = pd.to_numeric(raw["B365AHA"], errors="coerce").values if "B365AHA" in raw else np.nan
    if "Time" in raw.columns:
        out["time"] = raw["Time"].values
    return out


def load_all(leagues=None, seasons=None, raw_dir: Path = RAW) -> pd.DataFrame:
    leagues = leagues or list(LEAGUES)
    seasons = seasons or SEASONS
    frames = []
    for s in seasons:
        for lg in leagues:
            p = raw_dir / s / f"{lg}.csv"
            if p.exists():
                frames.append(load_file(p, lg, s))
    df = pd.concat(frames, ignore_index=True)
    # odds < 1.01 of > 1000 zijn datafouten
    odds_cols = [c for c in df.columns if c[-2:] in ("_h", "_d", "_a", "_o", "_u")]
    odds_cols += [c for c in AHMAP if c not in ("ah_line", "ahc_line")] + ["soft_ahh", "soft_aha"]
    df[odds_cols] = df[odds_cols].where((df[odds_cols] > 1.01) & (df[odds_cols] < 1000))
    df = df.sort_values(["date", "league", "home"]).reset_index(drop=True)
    df["match_id"] = (df.league + "_" + df.date.dt.strftime("%Y%m%d") + "_" + df.home + "_" + df.away)
    return df

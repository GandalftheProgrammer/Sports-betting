"""Strategieën: elke strategie zet wedstrijden om in kandidaat-weddenschappen.

Een weddenschap = (rij-index, markt, selectie, koers, geschatte kans).
De backtester bepaalt daarna inzet en resultaat. Strategieën mogen alleen
informatie gebruiken die vóór de wedstrijd bekend was: de 'open' koersen
(snapshot vóór de wedstrijd) en het model. Slotkoersen (psc_*) worden
uitsluitend gebruikt om achteraf de Closing Line Value te meten.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .features import SEL_1X2, SEL_OU

MARKETS = {"1x2": SEL_1X2, "ou": SEL_OU}


def _stack(df: pd.DataFrame, book: str, prob_prefix: str, markets) -> pd.DataFrame:
    parts = []
    for mkt in markets:
        for s in MARKETS[mkt]:
            parts.append(pd.DataFrame({
                "row": df.index,
                "market": mkt,
                "sel": s,
                "odds": df[f"{book}_{s}"].values,
                "prob": df[f"{prob_prefix}_{s}"].values,
            }))
    out = pd.concat(parts, ignore_index=True)
    return out.dropna(subset=["odds", "prob"])


@dataclass
class Strategy:
    name: str = "base"
    params: dict = field(default_factory=dict)

    def bets(self, df: pd.DataFrame) -> pd.DataFrame:  # pragma: no cover
        raise NotImplementedError


@dataclass
class ValueVsSharp(Strategy):
    """Kern-strategie: wed bij een 'soft' bookmaker als die een hogere koers
    biedt dan de eerlijke koers volgens Pinnacle (scherpe markt).

    params: book (b365|max|avg), min_edge, max_odds, min_odds, markets
    """
    name: str = "value_vs_sharp"

    def bets(self, df):
        p = {"book": "b365", "min_edge": 0.03, "max_odds": 5.0, "min_odds": 1.3,
             "markets": ("1x2",), **self.params}
        b = _stack(df, p["book"], "fair", p["markets"])
        b["edge"] = b.prob * b.odds - 1
        keep = (b.edge >= p["min_edge"]) & b.odds.between(p["min_odds"], p["max_odds"])
        if p.get("max_edge"):
            keep &= b.edge <= p["max_edge"]  # extreem hoge edges zijn vaak foute koersen
        return b[keep]


@dataclass
class ModelValue(Strategy):
    """Eigen model vs. markt. weight=1 -> puur model, 0 -> puur Pinnacle.
    Wed bij `book` als de (gemengde) kans een edge geeft."""
    name: str = "model_value"

    def bets(self, df):
        p = {"book": "b365", "weight": 0.3, "min_edge": 0.03, "max_odds": 5.0,
             "min_odds": 1.3, "markets": ("1x2",), **self.params}
        df = df.copy()
        for mkt in p["markets"]:
            for s in MARKETS[mkt]:
                df[f"blend_{s}"] = p["weight"] * df[f"m_{s}"] + (1 - p["weight"]) * df[f"fair_{s}"]
        b = _stack(df, p["book"], "blend", p["markets"])
        b["edge"] = b.prob * b.odds - 1
        keep = (b.edge >= p["min_edge"]) & b.odds.between(p["min_odds"], p["max_odds"])
        return b[keep]


@dataclass
class OddsBand(Strategy):
    """Test van marktbiases: wed blind op alles in een koersband/selectie.
    Bijv. favorieten (odds 1.2-1.6), longshots (odds > 6), gelijkspel, uitploeg.
    params: book, sels, min_odds, max_odds, markets, leagues"""
    name: str = "odds_band"

    def bets(self, df):
        p = {"book": "ps", "sels": ("h", "d", "a"), "min_odds": 1.0, "max_odds": 100.0,
             "markets": ("1x2",), "leagues": None, **self.params}
        if p["leagues"]:
            df = df[df.league.isin(p["leagues"])]
        b = _stack(df, p["book"], "fair", p["markets"])
        b["edge"] = b.prob * b.odds - 1
        keep = b.sel.isin(p["sels"]) & b.odds.between(p["min_odds"], p["max_odds"])
        return b[keep]


@dataclass
class Arbitrage(Strategy):
    """Zekere weddenschappen: som(1/beste koers) < 1 over alle uitkomsten.
    Let op: 'max' koersen komen van verschillende bookmakers en zijn in de
    praktijk vaak al weg of gelimiteerd. Geeft per arb alle benen terug, met
    inzetverdeling zodat de uitbetaling gelijk is."""
    name: str = "arbitrage"

    def bets(self, df):
        p = {"book": "max", "min_margin": 0.01, "markets": ("1x2", "ou"), **self.params}
        parts = []
        for mkt in p["markets"]:
            sels = MARKETS[mkt]
            odds = df[[f"{p['book']}_{s}" for s in sels]]
            inv = (1 / odds).sum(axis=1, min_count=len(sels))  # NaN als een koers ontbreekt
            arb = df.index[(inv < 1 - p["min_margin"]).fillna(False).values]
            for s in sels:
                o = df.loc[arb, f"{p['book']}_{s}"]
                parts.append(pd.DataFrame({
                    "row": arb, "market": mkt, "sel": s, "odds": o.values,
                    # 'prob' = aandeel van de inzet voor dit been
                    "prob": (1 / o / inv.loc[arb]).values,
                    "edge": (1 / inv.loc[arb] - 1).values,
                    "arb": True,
                }))
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def make(name: str, **params) -> Strategy:
    cls = {"value_vs_sharp": ValueVsSharp, "model_value": ModelValue,
           "odds_band": OddsBand, "arbitrage": Arbitrage}[name]
    return cls(params=params)


def outcome_won(df: pd.DataFrame, bets: pd.DataFrame) -> np.ndarray:
    r = df.loc[bets.row]
    goals = (r.fthg + r.ftag).values
    ftr = r.ftr.values
    sel = bets.sel.values
    return np.select(
        [sel == "h", sel == "d", sel == "a", sel == "o", sel == "u"],
        [ftr == "H", ftr == "D", ftr == "A", goals > 2.5, goals < 2.5],
        False,
    )

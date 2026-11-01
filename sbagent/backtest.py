"""Chronologische bankroll-simulatie.

- Inzetten worden per speeldag bepaald op basis van de bankroll aan het begin
  van die dag (je weet de uitslagen van vandaag nog niet).
- Staking: 'flat' (vast % van startbankroll), 'pct' (vast % van huidige
  bankroll) of 'kelly' (fractionele Kelly), altijd met een plafond per bet,
  een plafond per dag en een minimum inzet.
- `max_stake_abs` simuleert bookmakerlimieten.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

from .strategies import unit_return


@dataclass
class Staking:
    method: str = "kelly"       # kelly | pct | flat
    kelly_frac: float = 0.25
    pct: float = 0.01
    max_bet_frac: float = 0.03  # max 3% van bankroll per bet
    max_day_frac: float = 0.25  # max 25% van bankroll in omloop per dag
    min_stake: float = 0.5
    max_stake_abs: float = 200.0
    round_to: float = 0.1


def _raw_fraction(b: pd.DataFrame, st: Staking) -> np.ndarray:
    if "arb" in b and b["arb"].fillna(False).any():
        # arbitrage: totaal st.pct van bankroll per arb, verdeeld over de benen
        return st.pct * b.prob.values
    if st.method == "kelly":
        f = (b.prob * b.odds - 1) / (b.odds - 1)
        return np.clip(f.values * st.kelly_frac, 0, None)
    return np.full(len(b), st.pct)


def simulate(df: pd.DataFrame, bets: pd.DataFrame, bankroll: float = 100.0,
             staking: Staking | None = None) -> pd.DataFrame:
    st = staking or Staking()
    if bets is None or len(bets) == 0:
        return pd.DataFrame(columns=["date", "stake", "pnl", "bankroll"])
    b = bets.copy()
    b["date"] = df.loc[b.row, "date"].values
    b["ret"] = unit_return(df, b)
    b["won"] = b.ret > 0
    b["frac"] = _raw_fraction(b, st)
    b = b.sort_values(["date", "row"]).reset_index(drop=True)

    bank = bankroll
    start = bankroll
    stakes = np.zeros(len(b))
    pnls = np.zeros(len(b))
    banks = np.zeros(len(b))
    for _, idx in b.groupby("date", sort=True).indices.items():
        base = start if st.method == "flat" else bank
        f = np.minimum(b.frac.values[idx], st.max_bet_frac)
        s = f * base
        tot = s.sum()
        cap = st.max_day_frac * bank
        if tot > cap and tot > 0:
            s *= cap / tot
        s = np.minimum(s, st.max_stake_abs)
        s = np.floor(s / st.round_to) * st.round_to
        s[s < st.min_stake] = 0.0
        if s.sum() > bank:  # nooit meer inzetten dan je hebt
            s[:] = 0.0
        o = b.odds.values[idx]
        pnl = s * b.ret.values[idx]
        bank += pnl.sum()
        stakes[idx], pnls[idx], banks[idx] = s, pnl, bank
    b["stake"], b["pnl"], b["bankroll"] = stakes, pnls, banks
    return b[b.stake > 0].reset_index(drop=True)


def clv(df: pd.DataFrame, ledger: pd.DataFrame) -> np.ndarray:
    """Closing Line Value: genomen koers / eerlijke slotkoers (Pinnacle) - 1.
    Positieve CLV is de beste voorspeller van winst op lange termijn."""
    fc = np.array([df.at[r, f"refc_{s}"] if f"refc_{s}" in df else np.nan
                   for r, s in zip(ledger.row, ledger.sel)])
    if "line" in ledger:  # AH: alleen vergelijkbaar als de slotlijn gelijk is aan de genomen lijn
        same = np.array([df.at[r, "ahc_line"] for r in ledger.row]) == ledger.line.values
        fc = np.where(ledger.sel.isin(("ahh", "aha")).values & ~same, np.nan, fc)
    return ledger.odds.values * fc - 1


def metrics(df: pd.DataFrame, ledger: pd.DataFrame, bankroll: float = 100.0) -> dict:
    if len(ledger) == 0:
        return {"n_bets": 0, "turnover": 0, "profit": 0, "yield": np.nan, "final": bankroll,
                "roi_bankroll": 0, "max_dd": 0, "clv": np.nan, "hit": np.nan, "t_stat": np.nan,
                "avg_odds": np.nan, "flat_yield": np.nan}
    turnover = ledger.stake.sum()
    profit = ledger.pnl.sum()
    curve = np.concatenate([[bankroll], ledger.bankroll.values])
    peak = np.maximum.accumulate(curve)
    dd = ((peak - curve) / peak).max()
    # vlakke-inzet rendement per bet (1 eenheid), onafhankelijk van staking
    flat = ledger.ret.values
    t = flat.mean() / (flat.std(ddof=1) / np.sqrt(len(flat))) if len(flat) > 1 else np.nan
    c = clv(df, ledger)
    return {
        "n_bets": int(len(ledger)),
        "turnover": round(float(turnover), 2),
        "profit": round(float(profit), 2),
        "yield": round(float(profit / turnover), 4) if turnover else np.nan,
        "final": round(float(curve[-1]), 2),
        "roi_bankroll": round(float(curve[-1] / bankroll - 1), 4),
        "max_dd": round(float(dd), 4),
        "clv": round(float(np.nanmean(c)), 4),
        "hit": round(float(ledger.won.mean()), 4),
        "avg_odds": round(float(ledger.odds.mean()), 3),
        "flat_yield": round(float(flat.mean()), 4),
        "t_stat": round(float(t), 2),
    }


def staking_dict(st: Staking) -> dict:
    return asdict(st)

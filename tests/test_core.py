import numpy as np
import pandas as pd

from sbagent.backtest import Staking, simulate
from sbagent.devig import fair_probs
from sbagent.model import PoissonRatings, outcome_probs


def test_devig_sums_to_one_and_removes_margin():
    odds = np.array([[1.9, 3.6, 4.2], [1.25, 6.0, 11.0]])
    for m in ("mult", "power", "shin"):
        p = fair_probs(odds, m)
        assert np.allclose(p.sum(axis=1), 1)
        assert (p < 1 / odds * 1.0001).all()  # eerlijke kans < geïmpliceerde kans


def test_power_shifts_margin_to_longshot():
    odds = np.array([[1.25, 6.0, 11.0]])
    pm, pp = fair_probs(odds, "mult"), fair_probs(odds, "power")
    assert pp[0, 0] > pm[0, 0] and pp[0, 2] < pm[0, 2]


def test_outcome_probs_valid():
    ph, pd_, pa, po = outcome_probs(1.6, 1.1)
    assert abs(ph + pd_ + pa - 1) < 1e-4 and ph > pa and 0 < po < 1


def _toy():
    rows = []
    d = pd.Timestamp("2020-01-01")
    for i in range(40):
        rows.append(dict(date=d + pd.Timedelta(days=7 * i), league="X", season="1920",
                         home="A" if i % 2 else "B", away="B" if i % 2 else "A",
                         fthg=3 if i % 2 else 0, ftag=0 if i % 2 else 3))
    df = pd.DataFrame(rows)
    df["ftr"] = np.where(df.fthg > df.ftag, "H", "A")
    return df


def test_model_no_lookahead():
    df = _toy()
    full = PoissonRatings().run(df)
    part = PoissonRatings().run(df.iloc[:20])
    # voorspellingen voor de eerste 20 wedstrijden mogen niet afhangen van latere uitslagen
    assert np.allclose(full.iloc[:20].values, part.values)
    # A wint altijd -> model moet A sterker gaan vinden
    assert full.m_h.iloc[-1] > full.m_a.iloc[-1]


def test_simulate_pnl_arithmetic():
    df = _toy()
    bets = pd.DataFrame({"row": [1, 2], "market": "1x2", "sel": ["h", "h"],
                         "odds": [2.0, 2.0], "prob": [0.6, 0.6]})
    led = simulate(df, bets, 100, Staking(method="flat", pct=0.05, max_bet_frac=0.05))
    # bet 1 (row 1, thuis wint) +5, bet 2 (row 2, uit wint) -5
    assert list(led.pnl) == [5.0, -5.0]
    assert led.bankroll.iloc[-1] == 100.0


def test_ah_settlement_quarter_lines():
    from sbagent.strategies import ah_return
    o = np.array([2.0])
    # thuis -0.25, gelijkspel: half push, half verlies
    assert ah_return(np.array([0.0]), np.array([-0.25]), o)[0] == -0.5
    # thuis -0.75, winst met 1: half winst, half push
    assert ah_return(np.array([1.0]), np.array([-0.75]), o)[0] == 0.5
    # thuis -1, winst met 1: push
    assert ah_return(np.array([1.0]), np.array([-1.0]), o)[0] == 0.0
    # +0.5 gelijkspel: winst
    assert ah_return(np.array([0.0]), np.array([0.5]), o)[0] == 1.0

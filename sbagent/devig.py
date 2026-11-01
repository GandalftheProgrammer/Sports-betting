"""Marge (vig/overround) uit bookmakerkoersen halen -> 'eerlijke' kansen.

Pinnacle's koersen zijn, na verwijderen van de marge, de beste publiek
beschikbare schatting van de echte kans (zie docs/RESEARCH.md). Er zijn
meerdere methoden; 'power' en 'shin' corrigeren voor de favourite-longshot
bias (marge zit onevenredig op de underdogs).
"""
from __future__ import annotations

import numpy as np


def multiplicative(odds: np.ndarray) -> np.ndarray:
    """odds: (n, k). Simpel proportioneel normaliseren."""
    inv = 1.0 / odds
    return inv / inv.sum(axis=1, keepdims=True)


def power(odds: np.ndarray, iters: int = 60) -> np.ndarray:
    """Zoek k zodat sum((1/o)^k) == 1 (bisectie, vectorized)."""
    inv = 1.0 / odds
    lo = np.full(len(odds), 0.5)
    hi = np.full(len(odds), 2.5)
    for _ in range(iters):
        mid = (lo + hi) / 2
        s = (inv ** mid[:, None]).sum(axis=1)
        # s > 1 -> exponent moet omhoog
        lo = np.where(s > 1, mid, lo)
        hi = np.where(s > 1, hi, mid)
    k = (lo + hi) / 2
    p = inv ** k[:, None]
    return p / p.sum(axis=1, keepdims=True)


def shin(odds: np.ndarray, iters: int = 60) -> np.ndarray:
    """Shin (1993) model: marge als gevolg van insider trading."""
    inv = 1.0 / odds
    n = inv.shape[1]
    if n < 3:
        return power(odds)
    booksum = inv.sum(axis=1, keepdims=True)
    z = np.zeros((len(odds), 1))
    for _ in range(iters):
        root = np.sqrt(z**2 + 4 * (1 - z) * inv**2 / booksum)
        z = np.clip((root.sum(axis=1, keepdims=True) - 2) / (n - 2), 0, 0.4)
    p = (np.sqrt(z**2 + 4 * (1 - z) * inv**2 / booksum) - z) / (2 * (1 - z))
    return p / p.sum(axis=1, keepdims=True)


METHODS = {"mult": multiplicative, "power": power, "shin": shin}


def fair_probs(odds: np.ndarray, method: str = "power") -> np.ndarray:
    odds = np.asarray(odds, dtype=float)
    out = np.full(odds.shape, np.nan)
    ok = np.isfinite(odds).all(axis=1)
    if ok.any():
        out[ok] = METHODS[method](odds[ok])
    return out

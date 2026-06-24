"""Générateur de données synthétiques — permet de faire tourner le MVP et les tests hors-ligne
(sans accès Binance). Produit des bougies OHLCV avec une tendance et du bruit déterministes.
"""

from __future__ import annotations

import math
import random

from app.domain.indicators import Candle


def generate_candles(
    n: int = 200, start: float = 60000.0, trend: float = 0.0008, seed: int = 42
) -> list[Candle]:
    """Génère `n` bougies pseudo-aléatoires reproductibles (seed fixe)."""
    rng = random.Random(seed)
    candles: list[Candle] = []
    price = start
    for i in range(n):
        drift = trend * price
        noise = rng.uniform(-1, 1) * price * 0.006
        wave = math.sin(i / 12) * price * 0.003
        open_ = price
        close = max(1.0, price + drift + noise + wave)
        high = max(open_, close) * (1 + abs(rng.uniform(0, 0.004)))
        low = min(open_, close) * (1 - abs(rng.uniform(0, 0.004)))
        volume = rng.uniform(10, 100)
        candles.append(Candle(open_, high, low, close, volume))
        price = close
    return candles

"""Confirmation multi-timeframe (Phase signal-quality).

Évalue le biais technique sur plusieurs unités de temps (1h, 4h, 1j) et mesure leur alignement.
Léger et déterministe : n'utilise que `domain.ta` (pas de LLM) pour rester rapide.
"""

from __future__ import annotations

import logging

from app.data import markets
from app.domain import ta
from app.models.signal import Direction

logger = logging.getLogger(__name__)

TIMEFRAMES = ["1h", "4h", "1d"]


def _bias(score: float) -> Direction:
    if score > 0.12:
        return Direction.BUY
    if score < -0.12:
        return Direction.SELL
    return Direction.HOLD


async def confirm(asset: str, primary: Direction) -> dict:
    """Compare le biais technique sur 1h/4h/1j à la direction principale.

    Retourne {aligned, total, details:{tf:bias}}. `aligned` = nb d'unités de temps confirmant
    la direction principale (ignoré si HOLD).
    """
    details: dict[str, str] = {}
    aligned = 0
    total = 0
    for tf in TIMEFRAMES:
        try:
            candles = await markets.load_candles(asset, interval=tf, limit=200)
            if len(candles) < 60:
                continue
            bias = _bias(ta.analyze(candles)["score"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("MTF %s %s échoué (%s)", asset, tf, exc)
            continue
        details[tf] = bias.value
        total += 1
        if primary != Direction.HOLD and bias == primary:
            aligned += 1
    return {"aligned": aligned, "total": total, "details": details}

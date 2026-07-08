"""Ingestion de marché en TEMPS RÉEL (crypto / Binance WebSocket).

Au démarrage de l'app, lance une tâche asyncio par paire (top cryptos) qui :
1. backfill l'historique via REST (`binance.fetch_klines`),
2. maintient un **cache mémoire** de bougies à jour via `binance.stream_klines`,
3. **pousse** chaque bougie clôturée aux clients WebSocket (`hub.broadcast_all`).

`markets.load_candles` lit ce cache quand il est frais → tout le pipeline (signaux, scan,
copilot, daily picks) devient temps réel sans modification. Hors crypto / hors live, le repli
REST existant reste utilisé.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque

from app.core.config import get_settings
from app.data import binance
from app.domain.indicators import Candle
from app.realtime.hub import get_hub

logger = logging.getLogger(__name__)

_MAXLEN = 300
_CACHE: dict[tuple[str, str], deque[Candle]] = {}
_FRESH: dict[tuple[str, str], float] = {}  # (symbol, interval) -> wall-clock de dernière MAJ
_TASKS: list[asyncio.Task] = []

# Durée approximative d'un intervalle (s) pour juger la fraîcheur du flux.
_INTERVAL_SECONDS = {
    "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400,
}


def _seconds(interval: str) -> int:
    return _INTERVAL_SECONDS.get(interval, 3600)


def get_cached(symbol: str, interval: str, limit: int | None = None) -> list[Candle] | None:
    """Bougies en cache pour (symbole, interval), ou None si absent."""
    dq = _CACHE.get((symbol.upper(), interval))
    if not dq:
        return None
    items = list(dq)
    return items[-limit:] if limit else items


def is_live(symbol: str, interval: str) -> bool:
    """Vrai si le flux a poussé une bougie récemment (< 3 intervalles + marge)."""
    ts = _FRESH.get((symbol.upper(), interval))
    if ts is None:
        return False
    return (time.time() - ts) < (3 * _seconds(interval) + 120)


def latest_snapshot() -> list[dict]:
    """Dernière bougie connue par symbole (pour initialiser l'UI dès la connexion WebSocket)."""
    out: list[dict] = []
    for (sym, itv), dq in _CACHE.items():
        if dq:
            c = dq[-1]
            out.append({
                "symbol": sym, "interval": itv,
                "open": c.open, "high": c.high, "low": c.low, "close": c.close, "volume": c.volume,
            })
    return out


def status() -> dict:
    """État de l'ingestion live (symboles + fraîcheur), pour visibilité/monitoring."""
    now = time.time()
    streams = [
        {
            "symbol": sym,
            "interval": itv,
            "candles": len(_CACHE.get((sym, itv), [])),
            "age_seconds": round(now - _FRESH.get((sym, itv), now), 1),
            "live": is_live(sym, itv),
        }
        for (sym, itv) in sorted(_CACHE.keys())
    ]
    return {"enabled": get_settings().live_ingestion_enabled, "streams": streams}


def _put(symbol: str, interval: str, candles: list[Candle], *, fresh: bool) -> None:
    key = (symbol.upper(), interval)
    dq = _CACHE.get(key)
    if dq is None:
        dq = deque(maxlen=_MAXLEN)
        _CACHE[key] = dq
    dq.extend(candles)
    if fresh:
        _FRESH[key] = time.time()


async def _run(symbol: str, interval: str) -> None:
    """Backfill puis flux WS continu pour une paire ; pousse chaque bougie clôturée."""
    try:
        history = await binance.fetch_klines(symbol, interval=interval, limit=_MAXLEN)
        # Le backfill REST est de la donnée réelle récente -> on le marque frais pour que le
        # pipeline utilise le cache dès le démarrage (le flux WS le rafraîchit ensuite).
        _put(symbol, interval, history, fresh=True)
        logger.info("Live backfill %s (%s) : %d bougies", symbol, interval, len(history))
    except Exception as exc:  # noqa: BLE001 — le flux peut quand même chauffer le cache
        logger.warning("Backfill live %s échoué (%s)", symbol, exc)

    hub = get_hub()
    async for candle in binance.stream_klines(symbol, interval):
        _put(symbol, interval, [candle], fresh=True)
        await hub.broadcast_all({
            "type": "candle",
            "data": {
                "symbol": symbol, "interval": interval,
                "open": candle.open, "high": candle.high, "low": candle.low,
                "close": candle.close, "volume": candle.volume,
            },
        })


async def start() -> None:
    """Lance l'ingestion live pour les top cryptos configurées."""
    s = get_settings()
    if not s.live_ingestion_enabled:
        return
    symbols = [x.strip() for x in s.live_symbols.split(",") if x.strip()]
    interval = s.live_interval
    for sym in symbols:
        _TASKS.append(asyncio.create_task(_run(sym, interval)))
    logger.info("Ingestion live démarrée : %d paires (%s)", len(symbols), interval)


async def stop() -> None:
    """Annule toutes les tâches de streaming."""
    for task in _TASKS:
        task.cancel()
    for task in _TASKS:
        try:
            await task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
    _TASKS.clear()

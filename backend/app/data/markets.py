"""Routage multi-marchés (Phase 2) : crypto / actions / forex.

Détermine la classe d'actif d'un symbole et charge les bougies via le bon connecteur :
- crypto  -> Binance (existant)
- actions -> Alpaca (si clé) sinon synthétique
- forex   -> OANDA (si clé) sinon synthétique

Tous les connecteurs dégradent gracieusement vers des données synthétiques hors-ligne.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.data import binance
from app.data.synthetic import generate_candles
from app.domain.indicators import Candle

logger = logging.getLogger(__name__)

_FOREX = {"EUR", "USD", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"}
_CRYPTO_QUOTE = {"USDT", "USDC", "BTC", "ETH", "BUSD"}


def asset_class(symbol: str) -> str:
    if "/" in symbol:
        base, quote = symbol.split("/", 1)
        if quote in _CRYPTO_QUOTE:
            return "crypto"
        if base in _FOREX and quote in _FOREX:
            return "forex"
        return "crypto"
    return "stock"  # ex. AAPL, TSLA


async def _alpaca_candles(symbol: str, interval: str, limit: int) -> list[Candle]:
    s = get_settings()
    if not s.alpaca_api_key:
        raise RuntimeError("pas de clé Alpaca")
    import httpx

    tf = {"5m": "5Min", "15m": "15Min", "1h": "1Hour", "4h": "4Hour", "1d": "1Day"}.get(interval, "1Hour")
    url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
    headers = {"APCA-API-KEY-ID": s.alpaca_api_key, "APCA-API-SECRET-KEY": s.alpaca_api_secret}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"timeframe": tf, "limit": limit}, headers=headers)
        resp.raise_for_status()
        bars = resp.json().get("bars", [])
    return [Candle(b["o"], b["h"], b["l"], b["c"], b["v"]) for b in bars]


async def _oanda_candles(symbol: str, interval: str, limit: int) -> list[Candle]:
    s = get_settings()
    if not s.oanda_api_key:
        raise RuntimeError("pas de clé OANDA")
    import httpx

    gran = {"5m": "M5", "15m": "M15", "1h": "H1", "4h": "H4", "1d": "D"}.get(interval, "H1")
    instr = symbol.replace("/", "_")
    url = f"https://api-fxtrade.oanda.com/v3/instruments/{instr}/candles"
    headers = {"Authorization": f"Bearer {s.oanda_api_key}"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params={"granularity": gran, "count": limit, "price": "M"}, headers=headers)
        resp.raise_for_status()
        candles = resp.json().get("candles", [])
    out = []
    for c in candles:
        m = c["mid"]
        out.append(Candle(float(m["o"]), float(m["h"]), float(m["l"]), float(m["c"]), float(c.get("volume", 0))))
    return out


async def load_candles(symbol: str, interval: str = "1h", limit: int = 200) -> list[Candle]:
    """Charge les bougies selon la classe d'actif, avec repli synthétique."""
    cls = asset_class(symbol)
    try:
        if cls == "crypto":
            candles = await binance.fetch_klines(symbol, interval=interval, limit=limit)
        elif cls == "stock":
            candles = await _alpaca_candles(symbol, interval, limit)
        elif cls == "forex":
            candles = await _oanda_candles(symbol, interval, limit)
        else:
            candles = []
        if len(candles) >= 60:
            return candles
        logger.warning("Backfill %s (%s) insuffisant, repli synthétique", symbol, cls)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Connecteur %s indisponible pour %s (%s), repli synthétique", cls, symbol, exc)
    # Repli déterministe (graine basée sur le symbole pour la cohérence par actif)
    return generate_candles(seed=abs(hash(symbol)) % 10_000)

"""Signaux lead inter-marchés (Phase 1) — contexte additionnel pour l'expert crypto.

Repli GRACIEUX systématique : toute indisponibilité réseau renvoie une valeur neutre (jamais
d'exception qui casserait la génération de signal). Cache TTL en mémoire (Redis en Phase 2).
"""

from __future__ import annotations

import logging
import time

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_cache: dict[str, tuple[float, object]] = {}


def _cache_get(key: str):
    item = _cache.get(key)
    if item and item[0] > time.time():
        return item[1]
    return None


def _cache_put(key: str, value, ttl: int) -> None:
    _cache[key] = (time.time() + ttl, value)


async def get_funding_rates(symbol: str) -> float | None:
    """Dernier funding rate Binance futures (ex. 0.0001 = 0.01%). None si indisponible.

    > +0.1% => marché long surchargé (contrarien baissier) ; < -0.05% => contrarien haussier.
    """
    base = symbol.split("/")[0].split("-")[0].upper()
    pair = f"{base}USDT"
    key = f"funding:{pair}"
    cached = _cache_get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    try:
        import httpx

        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        async with httpx.AsyncClient(timeout=6) as client:
            resp = await client.get(url, params={"symbol": pair, "limit": 1})
            resp.raise_for_status()
            data = resp.json()
        rate = float(data[-1]["fundingRate"]) if data else None
    except Exception as exc:  # noqa: BLE001 — repli gracieux
        logger.warning("Funding %s indisponible (%s)", pair, exc)
        rate = None
    _cache_put(key, rate, get_settings().cross_asset_ttl)
    return rate


async def get_dxy_signal() -> float | None:
    """Score directionnel du Dollar Index (DXY) [-1..+1]. DXY haussier -> baissier pour EUR/USD…"""
    key = "dxy"
    cached = _cache_get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    score = None
    try:
        from app.data import yahoo
        from app.domain import indicators as ind

        rows = await yahoo.fetch_ohlcv("DX-Y.NYB", "1d", limit=60)
        closes = [r["close"] for r in rows]
        if len(closes) >= 20:
            ema20 = ind.ema(closes, 20)[-1]
            score = max(-1.0, min(1.0, (closes[-1] - ema20) / ema20 * 20))  # écart % normalisé
    except Exception as exc:  # noqa: BLE001
        logger.warning("DXY indisponible (%s)", exc)
    _cache_put(key, score, get_settings().cross_asset_ttl)
    return score


async def get_spx_regime() -> str:
    """Régime de marché actions via S&P 500 vs EMA20 journalière : risk_on | risk_off | neutral."""
    key = "spx_regime"
    cached = _cache_get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    regime = "neutral"
    try:
        from app.data import yahoo
        from app.domain import indicators as ind

        rows = await yahoo.fetch_ohlcv("^GSPC", "1d", limit=60)
        closes = [r["close"] for r in rows]
        if len(closes) >= 20:
            ema20 = ind.ema(closes, 20)[-1]
            regime = "risk_on" if closes[-1] > ema20 * 1.005 else "risk_off" if closes[-1] < ema20 * 0.995 else "neutral"
    except Exception as exc:  # noqa: BLE001
        logger.warning("SPX régime indisponible (%s)", exc)
    _cache_put(key, regime, get_settings().cross_asset_ttl)
    return regime


async def get_btc_dominance() -> float | None:
    """Dominance BTC (%) via CoinGecko (gratuit, sans clé). None si indisponible."""
    key = "btc_dominance"
    cached = _cache_get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    dom = None
    try:
        import httpx

        async with httpx.AsyncClient(timeout=6) as client:
            resp = await client.get("https://api.coingecko.com/api/v3/global")
            resp.raise_for_status()
            dom = float(resp.json()["data"]["market_cap_percentage"]["btc"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("BTC dominance indisponible (%s)", exc)
    _cache_put(key, dom, get_settings().cross_asset_ttl)
    return dom


async def get_macro_snapshot() -> dict:
    """Snapshot macro caché (VIX, tendance des taux, inflation) — pour l'expert OR notamment.

    Les moteurs de l'or : taux réels (taux - inflation), stress de marché (VIX), dollar (DXY)."""
    key = "macro_snapshot"
    cached = _cache_get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    snap = {"vix": None, "rate_trend": None, "inflation": None}
    try:
        from app.data import macro as macro_mod

        snap = await macro_mod.fetch_macro_data()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Snapshot macro indisponible (%s)", exc)
    _cache_put(key, snap, get_settings().cross_asset_ttl)
    return snap


async def get_btc_lead() -> float | None:
    """Score directionnel BTC [-1..+1] (analyse technique). None si indisponible.

    Sert de filtre pour les altcoins : un altcoin ne doit pas être acheté quand BTC chute fort.
    """
    key = "btc_lead"
    cached = _cache_get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    try:
        from app.data import markets
        from app.domain import ta

        candles = await markets.load_candles("BTC/USDT", interval="1h", limit=200)
        score = ta.analyze(candles)["score"] if len(candles) >= 60 else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("BTC lead indisponible (%s)", exc)
        score = None
    _cache_put(key, score, get_settings().cross_asset_ttl)
    return score

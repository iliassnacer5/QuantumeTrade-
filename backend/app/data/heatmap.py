"""Heatmap marché : variation 24h par actif (Binance ticker 24h, repli synthétique)."""

from __future__ import annotations

import logging

from app.data import binance
from app.data.synthetic import generate_candles

logger = logging.getLogger(__name__)


async def _binance_24h(symbol: str) -> dict | None:
    import httpx

    url = "https://api.binance.com/api/v3/ticker/24hr"
    params = {"symbol": binance.to_binance_symbol(symbol)}
    async with httpx.AsyncClient(timeout=8) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        d = resp.json()
    return {
        "symbol": symbol,
        "price": float(d["lastPrice"]),
        "change_pct": round(float(d["priceChangePercent"]), 2),
    }


def _synthetic_24h(symbol: str) -> dict:
    candles = generate_candles(n=48, seed=abs(hash(symbol)) % 1000)
    first, last = candles[0].close, candles[-1].close
    return {
        "symbol": symbol,
        "price": round(last, 2),
        "change_pct": round((last - first) / first * 100, 2),
    }


async def get_heatmap(symbols: list[str]) -> list[dict]:
    out: list[dict] = []
    for sym in symbols[:20]:
        try:
            row = await _binance_24h(sym)
            out.append(row if row else _synthetic_24h(sym))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Heatmap %s: repli synthétique (%s)", sym, exc)
            out.append(_synthetic_24h(sym))
    return out

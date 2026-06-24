"""Heatmap marché multi-actifs : variation 24h par actif.

Route selon la classe d'actif : crypto -> Binance (ticker 24h), actions/forex -> Yahoo Finance
(variation = dernier close vs close précédent en journalier). Repli synthétique si indisponible.
"""

from __future__ import annotations

import logging

from app.data import binance, markets
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
        "asset_class": "crypto",
        "price": float(d["lastPrice"]),
        "change_pct": round(float(d["priceChangePercent"]), 2),
    }


async def _yahoo_24h(symbol: str, cls: str) -> dict | None:
    from app.data import yahoo

    rows = await yahoo.fetch_ohlcv(symbol, "1d", limit=3)
    if len(rows) < 2:
        return None
    prev, last = rows[-2]["close"], rows[-1]["close"]
    return {
        "symbol": symbol,
        "asset_class": cls,
        "price": round(last, 4),
        "change_pct": round((last - prev) / prev * 100, 2) if prev else 0.0,
    }


def _synthetic_24h(symbol: str, cls: str) -> dict:
    candles = generate_candles(n=48, seed=abs(hash(symbol)) % 1000)
    first, last = candles[0].close, candles[-1].close
    return {
        "symbol": symbol,
        "asset_class": cls,
        "price": round(last, 2),
        "change_pct": round((last - first) / first * 100, 2),
    }


async def get_heatmap(symbols: list[str]) -> list[dict]:
    out: list[dict] = []
    for sym in symbols[:24]:
        cls = markets.asset_class(sym)
        try:
            row = await (_binance_24h(sym) if cls == "crypto" else _yahoo_24h(sym, cls))
            out.append(row if row else _synthetic_24h(sym, cls))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Heatmap %s (%s): repli synthétique (%s)", sym, cls, exc)
            out.append(_synthetic_24h(sym, cls))
    return out

"""Tests de l'ingestion temps réel : cache live, lecture par load_candles, broadcast_all."""

from __future__ import annotations

import asyncio
import time

import pytest

from app.domain.indicators import Candle
from app.realtime import market_stream
from app.realtime.hub import ConnectionHub


@pytest.fixture(autouse=True)
def _clear_cache():
    market_stream._CACHE.clear()
    market_stream._FRESH.clear()
    yield
    market_stream._CACHE.clear()
    market_stream._FRESH.clear()


def _candles(n: int, base: float = 100.0) -> list[Candle]:
    return [Candle(base + i, base + i + 1, base + i - 1, base + i, 10.0) for i in range(n)]


def test_cache_put_get_and_freshness():
    market_stream._put("BTC/USDT", "1h", _candles(70), fresh=True)
    cached = market_stream.get_cached("BTC/USDT", "1h", limit=50)
    assert cached is not None and len(cached) == 50
    assert market_stream.is_live("BTC/USDT", "1h") is True
    assert market_stream.get_cached("ETH/USDT", "1h") is None


def test_is_live_expires():
    market_stream._put("BTC/USDT", "1h", _candles(5), fresh=True)
    # Simule une dernière mise à jour très ancienne -> plus "live".
    market_stream._FRESH[("BTC/USDT", "1h")] = time.time() - 10 * 3600
    assert market_stream.is_live("BTC/USDT", "1h") is False


def test_status_reports_streams():
    market_stream._put("BTC/USDT", "1h", _candles(80), fresh=True)
    st = market_stream.status()
    syms = {s["symbol"] for s in st["streams"]}
    assert "BTC/USDT" in syms
    assert any(s["live"] and s["candles"] == 80 for s in st["streams"])


@pytest.mark.asyncio
async def test_load_candles_uses_live_cache(monkeypatch):
    """Quand le flux est chaud, load_candles renvoie le cache sans appel REST."""
    from app.data import markets

    market_stream._put("BTC/USDT", "1h", _candles(120), fresh=True)

    async def _boom(*a, **k):  # le REST ne doit PAS être appelé
        raise AssertionError("fetch_klines ne devrait pas être appelé quand le cache est live")

    monkeypatch.setattr(markets.binance, "fetch_klines", _boom)
    out = await markets.load_candles("BTC/USDT", interval="1h", limit=100)
    assert len(out) == 100


@pytest.mark.asyncio
async def test_broadcast_all_reaches_all_tenants():
    hub = ConnectionHub()

    class _FakeWS:
        def __init__(self):
            self.sent = []

        async def accept(self):
            pass

        async def send_json(self, msg):
            self.sent.append(msg)

    a, b = _FakeWS(), _FakeWS()
    await hub.connect("tenant-a", a)  # type: ignore[arg-type]
    await hub.connect("tenant-b", b)  # type: ignore[arg-type]
    await hub.broadcast_all({"type": "candle", "data": {"symbol": "BTC/USDT"}})
    assert a.sent and b.sent
    assert a.sent[0]["type"] == "candle"

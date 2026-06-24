"""Tests : catalogue multi-marchés, mapping news, multi-timeframe, scan haute-conviction."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.data import news, symbols
from app.main import app
from app.models.signal import Direction
from app.signal_engine import mtf


def _h(client):
    import uuid
    r = client.post("/api/auth/register", json={"email": f"m{uuid.uuid4().hex[:8]}@t.com", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_symbol_catalog_classes():
    cat = symbols.catalog()
    assert "crypto" in cat and "forex" in cat and "stock" in cat
    assert "BTC/USDT" in cat["crypto"] and "EUR/USD" in cat["forex"] and "AAPL" in cat["stock"]


def test_symbol_search_and_normalize():
    assert all("BTC" in s["symbol"] for s in symbols.search("btc"))
    assert symbols.search(asset_class="forex") and all(s["asset_class"] == "forex" for s in symbols.search(asset_class="forex"))
    assert symbols.normalize("btcusdt") == "BTC/USDT"
    assert symbols.normalize("eur-usd") == "EUR/USD"


def test_news_query_mapping():
    assert "Bitcoin" in news._query_for("BTC/USDT")
    assert "forex" in news._query_for("EUR/USD")
    assert news._query_for("AAPL") == "AAPL"


def test_symbols_endpoint():
    client = TestClient(app)
    h = _h(client)
    data = client.get("/api/market/symbols", params={"asset_class": "crypto"}, headers=h).json()
    assert data["results"] and all(r["asset_class"] == "crypto" for r in data["results"])
    assert set(data["classes"]) >= {"crypto", "forex", "stock"}


@pytest.mark.asyncio
async def test_mtf_confirm_structure():
    conf = await mtf.confirm("BTC/USDT", Direction.BUY)
    assert "aligned" in conf and "total" in conf and "details" in conf
    assert conf["aligned"] <= conf["total"]


def test_scan_endpoint():
    client = TestClient(app)
    h = _h(client)
    r = client.get("/api/signals/scan", params={"asset_class": "crypto", "limit": 6}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert "count" in body and "high_conviction" in body and isinstance(body["results"], list)
    # le scan classe par conviction et expose le flag haute-conviction
    for res in body["results"]:
        assert "conviction" in res and "high_conviction" in res and "adx" in res
    # filtre haute-conviction
    r2 = client.get("/api/signals/scan", params={"asset_class": "crypto", "high_conviction_only": "true", "limit": 6}, headers=h)
    for res in r2.json()["results"]:
        assert res["high_conviction"] is True

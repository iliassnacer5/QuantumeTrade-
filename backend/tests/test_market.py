"""Test de l'endpoint OHLCV (repli synthétique, offline)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.store import reset_store


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    reset_store()

    async def fake(*a, **k):
        raise RuntimeError("offline")

    # Force le repli synthétique de l'OHLCV.
    monkeypatch.setattr("app.data.ohlcv._binance_ohlcv", fake)
    yield


def test_ohlcv_requires_auth():
    assert TestClient(app).get("/api/market/ohlcv").status_code == 401


def test_ohlcv_returns_candles():
    client = TestClient(app)
    r = client.post("/api/auth/register", json={"email": "c@test.com", "password": "password123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    resp = client.get("/api/market/ohlcv?asset=BTC/USDT&timeframe=swing&limit=120", headers=h)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 120
    first = data[0]
    assert {"time", "open", "high", "low", "close"} <= set(first)
    assert first["high"] >= first["low"]
    # Horodatages croissants
    assert data[1]["time"] > data[0]["time"]

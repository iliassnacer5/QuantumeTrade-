"""Test de l'ingestion OHLCV vers la couche SQL (SQLite)."""

import time

from app.repositories.sql import SqlMarketRepository, make_engine_sessionmaker


def test_upsert_ohlcv_idempotent(tmp_path):
    _, sm = make_engine_sessionmaker(f"sqlite:///{tmp_path / 'm.db'}")
    repo = SqlMarketRepository(sm)
    now = int(time.time())
    rows = [
        {"time": now + i * 3600, "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 10}
        for i in range(5)
    ]
    assert repo.upsert_ohlcv("BTC/USDT", "1h", rows) == 5
    assert repo.count("BTC/USDT", "1h") == 5
    # Réinsertion -> idempotent (pas de doublons)
    repo.upsert_ohlcv("BTC/USDT", "1h", rows)
    assert repo.count("BTC/USDT", "1h") == 5


import pytest


@pytest.mark.asyncio
async def test_publish_falls_back_to_hub(monkeypatch):
    """Sans Redis, bus.publish doit utiliser le hub en mémoire (pas d'erreur)."""
    from app.realtime import bus

    called = {}

    class FakeHub:
        async def broadcast(self, tenant, msg):
            called["tenant"] = tenant
            called["msg"] = msg

    monkeypatch.setattr("app.realtime.bus.get_hub", lambda: FakeHub())
    await bus.publish("t1", {"type": "signal"})
    assert called["tenant"] == "t1"

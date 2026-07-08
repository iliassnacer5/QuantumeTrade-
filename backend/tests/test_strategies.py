"""Tests de la bibliothèque de stratégies : signaux, backtest générique, endpoints."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.domain.indicators import Candle
from app.main import app
from app.models.signal import Direction
from app.strategies import get_strategy, list_strategies


def _uptrend(n: int = 120) -> list[Candle]:
    """Tendance haussière régulière (pour que les stratégies de tendance déclenchent un BUY)."""
    out = []
    p = 100.0
    for i in range(n):
        p += 0.8
        out.append(Candle(p - 0.3, p + 0.5, p - 0.6, p, 10.0))
    return out


def test_registry_has_strategies():
    ids = {s["id"] for s in list_strategies()}
    assert {"ichimoku", "mtf_ema", "volume_vwap", "smc_ob", "zscore",
            "regime_router", "gap_fill", "squeeze_breakout"} == ids


def test_gap_fill_detects_open_gap():
    """Gap haussier >0,3% non comblé -> SELL (comblement) ; pas de gap -> HOLD."""
    from app.strategies.library import gap_fill
    base = [Candle(100, 101, 99, 100, 10) for _ in range(10)]
    gap_up = base + [Candle(102, 103, 101.5, 102.5, 10)]  # ouvre +2% au-dessus du close 100
    assert gap_fill(gap_up) == Direction.SELL
    no_gap = base + [Candle(100.05, 101, 99.5, 100.2, 10)]
    assert gap_fill(no_gap) == Direction.HOLD


def test_squeeze_breakout_fires_on_compression_break():
    """Compression (range < 1,2×ATR) puis cassure -> signal directionnel."""
    from app.strategies.library import squeeze_breakout
    # Volatilité normale puis 8 bougies très serrées, puis cassure haussière franche.
    wide = [Candle(100 + (i % 3), 102 + (i % 3), 98 + (i % 3), 100 + (i % 3), 10) for i in range(25)]
    tight = [Candle(100, 100.4, 99.8, 100.1, 10) for _ in range(8)]
    breakout = [Candle(100.2, 103, 100.1, 102.8, 10)]
    assert squeeze_breakout(wide + tight + breakout) == Direction.BUY
    assert squeeze_breakout(wide + tight + [Candle(100, 100.3, 99.9, 100.05, 10)]) == Direction.HOLD


def test_strategies_expose_markets():
    for s in list_strategies():
        assert s["markets"], "chaque stratégie déclare ses marchés"
    gf = next(s for s in list_strategies() if s["id"] == "gap_fill")
    assert gf["markets"] == ["stock", "commodity"]  # l'or a des gaps de week-end aussi


def test_ichimoku_buys_in_uptrend():
    assert get_strategy("ichimoku").fn(_uptrend()) == Direction.BUY


def test_mtf_ema_buys_in_uptrend():
    assert get_strategy("mtf_ema").fn(_uptrend()) == Direction.BUY


def test_each_strategy_returns_direction():
    candles = _uptrend()
    for s in list_strategies():
        d = get_strategy(s["id"]).fn(candles)
        assert d in (Direction.BUY, Direction.SELL, Direction.HOLD)


# ---------------- Endpoints ----------------
def _pro(client: TestClient) -> dict:
    email = f"u{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.post("/api/billing/checkout/pro", headers=h).status_code == 200
    return h


def test_list_and_select_strategy():
    client = TestClient(app)
    h = _pro(client)
    assert client.get("/api/strategies", headers=h).json()["strategies"]
    assert client.post("/api/strategies/select?strategy=zscore", headers=h).json()["selected"] == "zscore"
    assert client.get("/api/strategies/selected", headers=h).json()["selected"] == "zscore"
    # stratégie inconnue -> 404
    assert client.post("/api/strategies/select?strategy=nope", headers=h).status_code == 404


async def test_strategy_backtest_generic(monkeypatch):
    """Backtest générique d'une stratégie via le moteur (données mockées montantes)."""
    from app.api import backtest as bt_api

    async def _hist(symbol, timeframe, limit=600):  # noqa: ANN001
        from datetime import UTC, datetime, timedelta
        base = datetime.now(UTC) - timedelta(hours=300)
        return [Candle(c.open, c.high, c.low, c.close, c.volume, timestamp=base + timedelta(hours=i))
                for i, c in enumerate(_uptrend(300))]

    monkeypatch.setattr(bt_api, "_load_history", _hist)
    client = TestClient(app)
    h = _pro(client)
    r = client.post("/api/strategies/backtest?symbol=BTC/USDT&strategy=ichimoku", headers=h)
    assert r.status_code == 200, r.text
    assert "metrics" in r.json() and r.json()["strategy"] == "ichimoku"

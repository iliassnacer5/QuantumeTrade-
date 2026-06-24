"""Tests unitaires pour les métriques de backtest."""

from datetime import datetime

from app.backtest.metrics import compute_metrics
from app.backtest.schemas import BacktestEquityPoint, BacktestTrade

def test_compute_metrics_empty():
    metrics = compute_metrics([], [], 10000.0)
    assert metrics.total_trades == 0
    assert metrics.total_pnl == 0.0

def test_compute_metrics_basic():
    trades = [
        BacktestTrade(
            id="1", symbol="BTC/USDT", direction="BUY",
            entry_time=datetime.now(), exit_time=datetime.now(),
            entry_price=50000, exit_price=51000,
            size=1.0, pnl=1000.0, pnl_pct=10.0, duration_minutes=60
        ),
        BacktestTrade(
            id="2", symbol="BTC/USDT", direction="SELL",
            entry_time=datetime.now(), exit_time=datetime.now(),
            entry_price=51000, exit_price=51500,
            size=1.0, pnl=-500.0, pnl_pct=-5.0, duration_minutes=60
        ),
    ]
    
    equity = [
        BacktestEquityPoint(timestamp=datetime.now(), equity=10000.0, drawdown_pct=0.0),
        BacktestEquityPoint(timestamp=datetime.now(), equity=11000.0, drawdown_pct=0.0),
        BacktestEquityPoint(timestamp=datetime.now(), equity=10500.0, drawdown_pct=4.54),
    ]
    
    metrics = compute_metrics(trades, equity, 10000.0)
    
    assert metrics.total_trades == 2
    assert metrics.win_rate == 0.5
    assert metrics.profit_factor == 2.0  # 1000 / 500
    assert metrics.total_pnl == 500.0
    assert metrics.total_pnl_pct == 5.0
    assert metrics.max_drawdown_pct == 4.54
    assert metrics.average_win == 1000.0
    assert metrics.average_loss == 500.0

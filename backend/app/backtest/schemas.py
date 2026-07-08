"""Schémas Pydantic pour le moteur de backtest."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

class BacktestConfig(BaseModel):
    """Configuration d'un backtest."""
    symbol: str
    timeframe: str = "1h"
    start_time: datetime
    end_time: datetime
    initial_capital: float = 10000.0
    risk_per_trade_pct: float = 1.0
    use_llm: bool = False
    agent_weights: dict[str, float] | None = None

class BacktestTrade(BaseModel):
    """Un trade exécuté pendant le backtest."""
    id: str
    symbol: str
    direction: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    duration_minutes: float
    signal_rationale: str | None = None

class BacktestEquityPoint(BaseModel):
    """Point de la courbe d'équité."""
    timestamp: datetime
    equity: float
    drawdown_pct: float

class BacktestMetrics(BaseModel):
    """Métriques KPI globales."""
    total_trades: int
    win_rate: float
    profit_factor: float
    total_pnl: float
    total_pnl_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    average_win: float
    average_loss: float
    expectancy: float

class BacktestReport(BaseModel):
    """Rapport complet généré par l'engine."""
    id: str
    tenant_id: str
    config: BacktestConfig
    metrics: BacktestMetrics
    trades: list[BacktestTrade]
    equity_curve: list[BacktestEquityPoint]
    # Honnêteté : performance d'un simple « acheter & garder » sur la même période + surperformance.
    benchmark_pnl_pct: float = 0.0
    alpha_pct: float = 0.0  # total_pnl_pct - benchmark_pnl_pct (la valeur réellement ajoutée)
    # Coûts de transaction appliqués (frais + slippage, par côté, en %).
    cost_pct_per_side: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

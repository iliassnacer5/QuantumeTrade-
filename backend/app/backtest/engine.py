"""Moteur de backtest (Event-driven / Replay)."""

from __future__ import annotations

import logging
from datetime import timedelta
from uuid import uuid4

from contextlib import contextmanager

from app.backtest.metrics import compute_metrics
from app.backtest.schemas import BacktestConfig, BacktestEquityPoint, BacktestReport, BacktestTrade
from app.core.config import get_settings
from app.domain.indicators import Candle
from app.domain.risk import RiskParams
from app.models.signal import Direction
from app.signal_engine import engine as signal_engine

logger = logging.getLogger(__name__)


@contextmanager
def _llm_mode(enabled: bool):
    """Force (dé)active le LLM pour la durée du backtest.

    Par défaut un backtest tourne en mode déterministe (`use_llm=False`) : sans cela, chaque
    bougie déclencherait un appel réseau LLM par agent → exécution de plusieurs minutes et
    résultats non reproductibles. On restaure l'état global à la sortie.
    """
    settings = get_settings()
    previous = settings.llm_enabled
    settings.llm_enabled = enabled
    try:
        yield
    finally:
        settings.llm_enabled = previous


async def run_backtest(
    config: BacktestConfig,
    candles: list[Candle],
    tenant_id: str = "local",
) -> BacktestReport:
    """
    Exécute un backtest sur l'historique fourni en rejouant les bougies.
    Utilise le même SignalEngine que le live (déterministe sauf si `config.use_llm`).
    """
    with _llm_mode(config.use_llm):
        return await _run_backtest_inner(config, candles, tenant_id)


async def _run_backtest_inner(
    config: BacktestConfig,
    candles: list[Candle],
    tenant_id: str,
) -> BacktestReport:
    trades: list[BacktestTrade] = []
    equity_points: list[BacktestEquityPoint] = []

    capital = config.initial_capital
    peak_capital = capital
    current_position = None

    # Paramètres de risque par défaut pour le backtest
    risk = RiskParams(
        capital=capital,
        risk_per_trade_pct=config.risk_per_trade_pct,
    )

    # Horodatage robuste : utilise candle.timestamp si présent, sinon synthétise (1h/bougie).
    def cts(idx: int):
        c = candles[idx]
        return c.timestamp or (config.start_time + timedelta(hours=idx))

    # Historique de travail pour l'engine (besoin d'au moins 50 bougies pour les EMA)
    window_size = 60

    for i in range(window_size, len(candles)):
        current_candle = candles[i]
        history = candles[i - window_size : i + 1]
        
        # Enregistrer l'équité à chaque étape (simplifié : mark-to-market sur position ouverte)
        current_equity = capital
        if current_position:
            # PnL latent (approximatif)
            if current_position["direction"] == Direction.BUY.value:
                latent = (current_candle.close - current_position["entry_price"]) * current_position["size"]
            else:
                latent = (current_position["entry_price"] - current_candle.close) * current_position["size"]
            current_equity += latent
        
        peak_capital = max(peak_capital, current_equity)
        drawdown = ((peak_capital - current_equity) / peak_capital) * 100 if peak_capital > 0 else 0
        
        equity_points.append(BacktestEquityPoint(
            timestamp=cts(i),
            equity=round(current_equity, 2),
            drawdown_pct=round(drawdown, 2)
        ))
        
        # Gestion position existante (Stop Loss / Take Profit)
        if current_position:
            exit_price = None
            if current_position["direction"] == Direction.BUY.value:
                if current_candle.low <= current_position["stop_loss"]:
                    exit_price = current_position["stop_loss"]
                elif current_position["take_profit"] and current_candle.high >= current_position["take_profit"]:
                    exit_price = current_position["take_profit"]
            else:
                if current_candle.high >= current_position["stop_loss"]:
                    exit_price = current_position["stop_loss"]
                elif current_position["take_profit"] and current_candle.low <= current_position["take_profit"]:
                    exit_price = current_position["take_profit"]
            
            if exit_price is not None:
                # Clôture
                pnl = (exit_price - current_position["entry_price"]) * current_position["size"]
                if current_position["direction"] == Direction.SELL.value:
                    pnl = -pnl
                    
                capital += pnl
                risk.capital = capital # Mise à jour capital
                
                duration = (cts(i) - current_position["entry_time"]).total_seconds() / 60.0
                
                trades.append(BacktestTrade(
                    id=str(uuid4()),
                    symbol=config.symbol,
                    direction=current_position["direction"],
                    entry_time=current_position["entry_time"],
                    exit_time=cts(i),
                    entry_price=current_position["entry_price"],
                    exit_price=exit_price,
                    size=current_position["size"],
                    pnl=round(pnl, 2),
                    pnl_pct=round((pnl / capital * 100) if capital else 0.0, 2),
                    duration_minutes=round(duration, 2),
                    signal_rationale=current_position["rationale"]
                ))
                current_position = None
                continue
        
        # Pas de position -> Chercher un signal (mode LLM piloté par config.use_llm via _llm_mode)
        if not current_position:
            try:
                signal = await signal_engine.generate_signal(
                    asset=config.symbol,
                    candles=history,
                    risk=risk,
                    weights=config.agent_weights
                )
                
                if signal.direction != Direction.HOLD and signal.confidence >= 60:
                    current_position = {
                        "direction": signal.direction.value,
                        "entry_price": current_candle.close,
                        "stop_loss": signal.stop_loss,
                        "take_profit": signal.take_profit_1,
                        "size": signal.position_size or 0,
                        "entry_time": cts(i),
                        "rationale": signal.rationale
                    }
            except Exception as e:
                logger.error(f"Erreur backtest signal generation at {current_candle.timestamp}: {e}")
                
    # Clôture position finale si ouverte
    if current_position:
        exit_price = candles[-1].close
        pnl = (exit_price - current_position["entry_price"]) * current_position["size"]
        if current_position["direction"] == Direction.SELL.value:
            pnl = -pnl
        capital += pnl
        duration = (cts(len(candles)-1) - current_position["entry_time"]).total_seconds() / 60.0
        trades.append(BacktestTrade(
            id=str(uuid4()),
            symbol=config.symbol,
            direction=current_position["direction"],
            entry_time=current_position["entry_time"],
            exit_time=cts(len(candles)-1),
            entry_price=current_position["entry_price"],
            exit_price=exit_price,
            size=current_position["size"],
            pnl=round(pnl, 2),
            pnl_pct=round((pnl / capital * 100) if capital else 0.0, 2),
            duration_minutes=round(duration, 2),
            signal_rationale=current_position["rationale"]
        ))
        
    metrics = compute_metrics(trades, equity_points, config.initial_capital)
    
    return BacktestReport(
        id=str(uuid4()),
        tenant_id=tenant_id,
        config=config,
        metrics=metrics,
        trades=trades,
        equity_curve=equity_points
    )

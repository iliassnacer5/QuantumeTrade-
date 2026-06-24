"""M3 — Signal Engine.

Orchestre les agents, applique l'arbitrage du Master Agent, calcule les niveaux de risque
(déterministe) et produit une `SignalCard` consolidée et explicable.
"""

from __future__ import annotations

from app.agents import master, sentiment, technical
from app.agents.sentiment import NewsItem
from app.domain import indicators as ind
from app.domain.indicators import Candle
from app.domain.risk import RiskParams, compute_levels
from app.models.signal import Direction, SignalCard, Timeframe


async def generate_signal(
    *,
    asset: str,
    candles: list[Candle],
    news: list[NewsItem] | None = None,
    fear_greed: int | None = None,
    risk: RiskParams,
    timeframe: Timeframe = Timeframe.SWING,
    weights: dict[str, float] | None = None,
) -> SignalCard:
    """Produit une Signal Card à partir des données de marché et de sentiment."""
    news = news or []

    # 1. Agents en parallèle (logiquement) -> sorties normalisées
    tech_out = await technical.run(candles)
    sent_out = await sentiment.run(news, fear_greed)

    # 2. Arbitrage Master
    decision = master.decide([tech_out, sent_out], weights)

    entry = candles[-1].close
    atr_val = ind.atr(candles, 14) or (entry * 0.01)  # fallback volatilité 1%

    # 3. Niveaux de risque déterministes
    if decision.direction == Direction.HOLD:
        # Pas de position : niveaux indicatifs neutres autour de l'entrée.
        return SignalCard(
            asset=asset,
            direction=Direction.HOLD,
            entry=round(entry, 8),
            stop_loss=round(entry, 8),
            take_profit_1=round(entry, 8),
            risk_reward=0.0,
            confidence=decision.confidence,
            timeframe=timeframe,
            rationale=decision.rationale,
        )

    levels = compute_levels(decision.direction, entry, atr_val, risk)

    return SignalCard(
        asset=asset,
        direction=decision.direction,
        entry=round(entry, 8),
        stop_loss=levels.stop_loss,
        take_profit_1=levels.take_profit_1,
        take_profit_2=levels.take_profit_2,
        take_profit_3=levels.take_profit_3,
        risk_reward=levels.risk_reward,
        confidence=decision.confidence,
        timeframe=timeframe,
        rationale=decision.rationale,
    )

"""Schéma de la Signal Card — sortie structurée et stricte du Signal Engine.

Ce schéma est le contrat partagé entre les agents, l'API et le frontend.
"""

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class Timeframe(str, Enum):
    SCALP = "scalp"
    INTRADAY = "intraday"
    SWING = "swing"
    POSITION = "position"


class SignalCard(BaseModel):
    """Unité d'information centrale présentée au trader."""

    asset: str = Field(..., examples=["BTC/USDT"])
    direction: Direction
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float | None = None
    take_profit_3: float | None = None
    risk_reward: float = Field(..., description="Ratio risque/rendement, ex. 3.2")
    confidence: int = Field(..., ge=0, le=100, description="Score de confiance 0-100%")
    timeframe: Timeframe
    rationale: str = Field(..., description="Justification IA en langage naturel")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

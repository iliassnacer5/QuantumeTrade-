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
    # Dimensionnement (Risk Management) — utile pour l'exposition / P&L
    position_size: float | None = Field(default=None, description="Quantité d'actif")
    position_value: float | None = Field(default=None, description="Valeur de la position en devise")
    risk_amount: float | None = Field(default=None, description="Montant risqué en devise")
    risk_warning: str | None = Field(default=None, description="Avertissement de risque éventuel")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

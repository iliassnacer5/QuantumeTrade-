"""Validation du schéma SignalCard."""

import pytest
from pydantic import ValidationError

from app.models.signal import Direction, SignalCard, Timeframe


def test_signal_card_valid():
    card = SignalCard(
        asset="BTC/USDT",
        direction=Direction.BUY,
        entry=64250,
        stop_loss=62800,
        take_profit_1=66000,
        take_profit_2=68500,
        take_profit_3=71000,
        risk_reward=3.2,
        confidence=82,
        timeframe=Timeframe.SWING,
        rationale="Cassure de résistance + sentiment positif + momentum haussier",
    )
    assert card.direction == Direction.BUY
    assert 0 <= card.confidence <= 100


def test_confidence_out_of_range():
    with pytest.raises(ValidationError):
        SignalCard(
            asset="BTC/USDT",
            direction=Direction.BUY,
            entry=1,
            stop_loss=1,
            take_profit_1=1,
            risk_reward=1,
            confidence=150,  # invalide
            timeframe=Timeframe.SWING,
            rationale="x",
        )

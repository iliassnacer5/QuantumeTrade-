"""Tests unitaires pour l'agent Volume."""

import pytest
from app.agents import volume
from app.domain.indicators import Candle

@pytest.mark.asyncio
async def test_volume_agent_insufficient_data():
    candles = [
        Candle(open=100, high=101, low=99, close=100, volume=10)
    ]
    
    out = await volume.run(candles)
    assert out.name == "volume"
    assert "Données insuffisantes" in out.rationale

@pytest.mark.asyncio
async def test_volume_agent_neutral_without_volume():
    """Forex spot (volume=0) : l'agent doit rester NEUTRE, pas inventer une divergence."""
    candles = [Candle(open=100 + i, high=101 + i, low=99 + i, close=100 + i, volume=0) for i in range(25)]
    out = await volume.run(candles)
    assert out.score == 0.0
    assert "neutre" in out.rationale.lower()


@pytest.mark.asyncio
async def test_volume_agent_basic():
    # Génération de bougies avec tendance haussière (prix et volume)
    candles = []
    base_price = 100
    base_vol = 10
    
    for i in range(25):
        candles.append(Candle(
            open=base_price,
            high=base_price + 2,
            low=base_price - 1,
            close=base_price + 1,
            volume=base_vol
        ))
        base_price += 1
        base_vol += 1
        
    out = await volume.run(candles)
    
    # Avec une montée constante, l'OBV devrait être en hausse
    # et le prix au-dessus du VWAP (tendance positive continue)
    assert out.name == "volume"
    assert out.score > 0.0
    assert "OBV en hausse" in out.rationale
    assert out.confidence >= 0.4

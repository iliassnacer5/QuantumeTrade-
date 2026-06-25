"""Tests du module de gestion du risque (déterministe)."""

import pytest

from app.domain.risk import RiskParams, compute_levels, exposure_ok, historical_var
from app.models.signal import Direction


def test_buy_levels_ordering():
    p = RiskParams(capital=10000, risk_per_trade_pct=1.0)
    out = compute_levels(Direction.BUY, entry=100.0, atr=2.0, p=p)
    assert out.stop_loss < 100 < out.take_profit_1 < out.take_profit_2 < out.take_profit_3
    assert out.risk_reward >= 1.5  # tp1=2.5*atr, sl=1.5*atr -> R/R ≈ 1.67 (>= seuil checklist)


def test_sell_levels_inverted():
    p = RiskParams(capital=10000)
    out = compute_levels(Direction.SELL, entry=100.0, atr=2.0, p=p)
    assert out.stop_loss > 100 > out.take_profit_1 > out.take_profit_3


def test_position_sizing_respects_risk():
    p = RiskParams(capital=10000, risk_per_trade_pct=1.0, atr_sl_mult=1.5)
    out = compute_levels(Direction.BUY, entry=100.0, atr=2.0, p=p)
    # Montant risqué = 1% de 10000 = 100 ; perte au SL = size * sl_dist doit valoir ~100
    sl_dist = abs(100 - out.stop_loss)
    assert round(out.position_size * sl_dist, 2) == 100.0
    assert out.risk_amount == 100.0


def test_atr_must_be_positive():
    with pytest.raises(ValueError):
        compute_levels(Direction.BUY, 100, 0, RiskParams(capital=1000))


def test_var_and_exposure():
    returns = [-0.05, -0.02, 0.01, 0.03, -0.10, 0.04]
    assert historical_var(returns, 0.95) >= 0
    assert exposure_ok(4000, 10000, 50.0) is True
    assert exposure_ok(6000, 10000, 50.0) is False

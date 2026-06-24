"""M4 — Risk Management : calculs déterministes (JAMAIS de LLM).

Dimensionnement de position, niveaux SL/TP basés sur l'ATR, ratio R/R, VaR simplifiée.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.signal import Direction


@dataclass
class RiskParams:
    """Paramètres de risque issus du profil de l'utilisateur."""

    capital: float
    risk_per_trade_pct: float = 1.0  # % du capital risqué par trade
    atr_sl_mult: float = 1.5  # SL = entrée -/+ atr_sl_mult * ATR
    atr_tp_mults: tuple[float, float, float] = (1.5, 3.0, 5.0)  # TP1/2/3


@dataclass
class RiskOutput:
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward: float
    position_size: float  # quantité d'actif
    position_value: float  # valeur en devise de cotation
    risk_amount: float  # montant risqué en devise


def compute_levels(direction: Direction, entry: float, atr: float, p: RiskParams) -> RiskOutput:
    """Calcule SL/TP, R/R et taille de position pour un signal directionnel.

    Pour HOLD, on retourne des niveaux neutres (pas de position).
    """
    if atr <= 0:
        raise ValueError("ATR doit être strictement positif")

    sign = 1 if direction == Direction.BUY else -1
    sl_dist = p.atr_sl_mult * atr
    stop_loss = entry - sign * sl_dist
    tp1 = entry + sign * p.atr_tp_mults[0] * atr
    tp2 = entry + sign * p.atr_tp_mults[1] * atr
    tp3 = entry + sign * p.atr_tp_mults[2] * atr

    reward = abs(tp1 - entry)
    risk = abs(entry - stop_loss)
    risk_reward = round(reward / risk, 2) if risk > 0 else 0.0

    # Dimensionnement : montant risqué = capital * risk% ; quantité = risque€ / distance SL
    risk_amount = p.capital * (p.risk_per_trade_pct / 100)
    position_size = risk_amount / sl_dist if sl_dist > 0 else 0.0
    position_value = position_size * entry

    return RiskOutput(
        stop_loss=round(stop_loss, 8),
        take_profit_1=round(tp1, 8),
        take_profit_2=round(tp2, 8),
        take_profit_3=round(tp3, 8),
        risk_reward=risk_reward,
        position_size=round(position_size, 8),
        position_value=round(position_value, 2),
        risk_amount=round(risk_amount, 2),
    )


def historical_var(returns: list[float], confidence: float = 0.95) -> float:
    """VaR historique simplifiée : perte au quantile (1-confidence). Valeur positive = perte."""
    if not returns:
        return 0.0
    ordered = sorted(returns)
    idx = int((1 - confidence) * len(ordered))
    idx = min(max(idx, 0), len(ordered) - 1)
    return abs(min(ordered[idx], 0.0))


def exposure_ok(open_positions_value: float, capital: float, max_exposure_pct: float = 50.0) -> bool:
    """Vérifie que l'exposition totale ne dépasse pas le plafond autorisé."""
    if capital <= 0:
        return False
    return (open_positions_value / capital) * 100 <= max_exposure_pct

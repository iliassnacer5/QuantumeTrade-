"""Agent Technique (M2).

Calcule des indicateurs déterministes (RSI, MACD, EMA, Bollinger) et en dérive un score
directionnel. Le LLM ne sert qu'à enrichir l'explication (jamais à calculer le signal).
"""

from __future__ import annotations

from app.agents.base import AgentOutput
from app.domain import indicators as ind
from app.domain.indicators import Candle


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


async def run(candles: list[Candle]) -> AgentOutput:
    closes = [c.close for c in candles]
    name = "technical"

    if len(closes) < 35:
        return AgentOutput(name, 0.0, 0.1, "Données insuffisantes pour l'analyse technique.")

    price = closes[-1]
    rsi_val = ind.rsi(closes, 14)
    macd_res = ind.macd(closes)
    ema_fast = ind.ema(closes, 20)[-1]
    ema_slow = ind.ema(closes, 50)[-1] if len(closes) >= 50 else ind.ema(closes, 20)[-1]
    boll = ind.bollinger(closes, 20)

    signals: list[float] = []
    notes: list[str] = []

    # Tendance EMA
    if ema_fast > ema_slow:
        signals.append(0.4)
        notes.append("EMA20 > EMA50 (tendance haussière)")
    else:
        signals.append(-0.4)
        notes.append("EMA20 < EMA50 (tendance baissière)")

    # RSI
    if rsi_val is not None:
        if rsi_val < 30:
            signals.append(0.5)
            notes.append(f"RSI {rsi_val:.0f} (survente)")
        elif rsi_val > 70:
            signals.append(-0.5)
            notes.append(f"RSI {rsi_val:.0f} (surachat)")
        else:
            tilt = (50 - rsi_val) / 100
            signals.append(tilt)
            notes.append(f"RSI {rsi_val:.0f} (neutre)")

    # MACD
    if macd_res is not None:
        _, _, hist = macd_res
        if hist > 0:
            signals.append(0.3)
            notes.append("MACD histogramme positif (momentum haussier)")
        else:
            signals.append(-0.3)
            notes.append("MACD histogramme négatif (momentum baissier)")

    # Bollinger
    if boll is not None:
        low, _, high = boll
        if price <= low:
            signals.append(0.3)
            notes.append("Prix sur bande basse de Bollinger")
        elif price >= high:
            signals.append(-0.3)
            notes.append("Prix sur bande haute de Bollinger")

    score = _clamp(sum(signals) / max(len(signals), 1))
    confidence = min(1.0, 0.4 + 0.15 * len(signals))
    rationale = "Analyse technique : " + " ; ".join(notes) + "."
    
    # Enrichissement LLM (optionnel)
    from app.agents import llm
    if llm.available() and notes:
        try:
            prompt = (
                f"Voici les signaux techniques détectés pour un actif (prix = {price}) : {', '.join(notes)}. "
                "Génère une explication concise (2 phrases max) du contexte technique. Ne donne pas de conseil d'investissement."
            )
            llm_rationale = await llm.complete(prompt, role="fast", max_tokens=100)
            if llm_rationale:
                rationale = llm_rationale.strip()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Erreur LLM technical : %s", e)

    return AgentOutput(
        name=name,
        score=round(score, 3),
        confidence=round(confidence, 3),
        rationale=rationale,
        details={"rsi": rsi_val, "ema_fast": ema_fast, "ema_slow": ema_slow, "price": price},
    )

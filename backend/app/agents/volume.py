"""Agent Volume (M2).

Analyse la pression d'achat/vente en utilisant les indicateurs de volume (OBV, VWAP).
Déterministe par défaut.
"""

from __future__ import annotations

from app.agents.base import AgentOutput, enrich
from app.domain import indicators as ind
from app.domain.indicators import Candle


def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


async def run(candles: list[Candle]) -> AgentOutput:
    name = "volume"
    if len(candles) < 20:
        return AgentOutput(name, 0.0, 0.1, "Données insuffisantes pour l'analyse de volume.")

    price = candles[-1].close
    obv_line = ind.obv(candles)
    vwap_val = ind.vwap(candles)
    
    signals: list[float] = []
    notes: list[str] = []

    # Analyse OBV (tendance)
    if len(obv_line) >= 10:
        obv_current = obv_line[-1]
        obv_past = obv_line[-10]
        if obv_current > obv_past:
            signals.append(0.3)
            notes.append("OBV en hausse (pression acheteuse)")
        elif obv_current < obv_past:
            signals.append(-0.3)
            notes.append("OBV en baisse (pression vendeuse)")
            
    # Analyse VWAP
    if vwap_val is not None:
        if price > vwap_val:
            signals.append(0.2)
            notes.append(f"Prix au-dessus du VWAP ({vwap_val:.2f})")
        else:
            signals.append(-0.2)
            notes.append(f"Prix en-dessous du VWAP ({vwap_val:.2f})")

    # Divergence prix / OBV (simplifiée)
    if len(obv_line) >= 5:
        price_trend = price > candles[-5].close
        obv_trend = obv_line[-1] > obv_line[-5]
        if price_trend and not obv_trend:
            signals.append(-0.4)
            notes.append("Divergence baissière Prix/OBV")
        elif not price_trend and obv_trend:
            signals.append(0.4)
            notes.append("Divergence haussière Prix/OBV")

    score = _clamp(sum(signals) / max(len(signals), 1))
    confidence = min(1.0, 0.4 + 0.15 * len(signals))
    rationale = "Analyse de volume : " + " ; ".join(notes) + "."

    # Enrichissement LLM optionnel (AJOUTÉ, jamais substitué)
    from app.agents import llm
    if llm.available() and notes:
        try:
            prompt = (
                f"Analyste volumes. Rédige UNE phrase complète de synthèse (français) sur la dynamique "
                f"des volumes, sans conseil : {', '.join(notes)}."
            )
            rationale = enrich(rationale, await llm.complete(prompt, role="fast", max_tokens=200))
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Erreur LLM volume : %s", e)

    return AgentOutput(
        name=name,
        score=round(score, 3),
        confidence=round(confidence, 3),
        rationale=rationale,
        details={"obv_current": obv_line[-1], "vwap": vwap_val},
    )

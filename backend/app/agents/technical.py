"""Agent Technique (M2).

Calcule une analyse technique experte complète (RSI, MACD, ADX, Stochastique, EMA, Bollinger, ATR,
OBV, VWAP, supports/résistances) via `domain.ta`, en dérive un score directionnel décisif, et expose
toutes les métriques. Le LLM ne sert qu'à AJOUTER un commentaire (jamais à remplacer l'analyse).
"""

from __future__ import annotations

import logging

from app.agents.base import AgentOutput, enrich
from app.domain import ta
from app.domain.indicators import Candle

logger = logging.getLogger(__name__)


async def run(candles: list[Candle]) -> AgentOutput:
    name = "technical"
    if len(candles) < 35:
        return AgentOutput(name, 0.0, 0.1, "Données insuffisantes pour l'analyse technique.")

    a = ta.analyze(candles)
    rationale = "Analyse technique : " + " ; ".join(a["notes"]) + "."

    from app.agents import llm
    if llm.available():
        try:
            prompt = (
                "Tu es analyste technique. À partir de ces signaux, rédige UNE phrase de synthèse "
                "claire et complète (français), sans conseil d'investissement :\n"
                + " ; ".join(a["notes"])
            )
            rationale = enrich(rationale, await llm.complete(prompt, role="fast", max_tokens=220))
        except Exception as e:  # noqa: BLE001
            logger.warning("Erreur LLM technical : %s", e)

    return AgentOutput(
        name=name,
        score=a["score"],
        confidence=a["confidence"],
        rationale=rationale,
        details=a["metrics"],
    )

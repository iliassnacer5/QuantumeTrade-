"""Agent Sentiment (M2).

Analyse une liste d'items de news (titre + score de sentiment éventuel) et produit un biais
de marché. Si les news n'ont pas de score, un lexique simple fournit un fallback déterministe.
En production : NLP/FinBERT ou LLM via LiteLLM pour le scoring fin.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentOutput

_BULLISH = {
    "surge", "rally", "soar", "gain", "bullish", "beat", "record", "upgrade",
    "adoption", "partnership", "approval", "inflow", "breakout", "all-time high",
}
_BEARISH = {
    "crash", "plunge", "drop", "fall", "bearish", "miss", "downgrade", "hack",
    "ban", "lawsuit", "outflow", "selloff", "fear", "liquidation", "dump",
}


@dataclass
class NewsItem:
    headline: str
    sentiment: float | None = None  # -1..+1 si déjà scoré


def _lexicon_score(headline: str) -> float:
    text = headline.lower()
    pos = sum(1 for w in _BULLISH if w in text)
    neg = sum(1 for w in _BEARISH if w in text)
    if pos == neg:
        return 0.0
    return (pos - neg) / (pos + neg)


async def run(news: list[NewsItem], fear_greed: int | None = None) -> AgentOutput:
    name = "sentiment"
    if not news and fear_greed is None:
        return AgentOutput(name, 0.0, 0.1, "Pas de news disponibles.")

    from app.agents import llm
    import json

    scores = []
    
    if llm.available() and news:
        try:
            headlines = [n.headline for n in news if n.sentiment is None]
            if headlines:
                prompt = (
                    "Score le sentiment financier global de ces titres d'actualité de -1.0 (très baissier) "
                    "à 1.0 (très haussier). Réponds UNIQUEMENT avec un nombre décimal."
                    f"\nTitres: {headlines}"
                )
                resp = await llm.complete(prompt, role="fast", max_tokens=10)
                try:
                    llm_score = float(resp.strip())
                    llm_score = max(-1.0, min(1.0, llm_score))
                    for n in news:
                        if n.sentiment is None:
                            n.sentiment = llm_score
                except ValueError:
                    pass # Fallback au lexique
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Erreur LLM sentiment : %s", e)

    scores = [n.sentiment if n.sentiment is not None else _lexicon_score(n.headline) for n in news]
    news_score = sum(scores) / len(scores) if scores else 0.0

    # Fear & Greed Index (0-100) -> contribue au biais (50 = neutre)
    fg_component = 0.0
    if fear_greed is not None:
        fg_component = (fear_greed - 50) / 50  # -1..+1

    if news and fear_greed is not None:
        score = 0.6 * news_score + 0.4 * fg_component
    elif news:
        score = news_score
    else:
        score = fg_component

    score = max(-1.0, min(1.0, score))
    confidence = min(1.0, 0.3 + 0.1 * len(news) + (0.2 if fear_greed is not None else 0))

    bias = "positif" if score > 0.1 else "négatif" if score < -0.1 else "neutre"
    parts = [f"Sentiment des news {bias} (n={len(news)})"]
    if fear_greed is not None:
        parts.append(f"Fear & Greed {fear_greed}/100")
    rationale = "Analyse de sentiment : " + " ; ".join(parts) + "."

    return AgentOutput(
        name=name,
        score=round(score, 3),
        confidence=round(confidence, 3),
        rationale=rationale,
        details={"news_count": len(news), "fear_greed": fear_greed},
    )

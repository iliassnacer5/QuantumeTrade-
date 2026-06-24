"""Agent Pattern (M2) — reconnaissance de figures chartistes.

Détection déterministe des figures chandeliers classiques (avalée, marteau, étoile filante, doji)
+ structure (plus hauts/bas). En production, l'option vision (Gemini 2.5 Pro) analyse une image du
graphe ; ici le cœur est déterministe et testable, l'appel vision est un enrichissement optionnel.
"""

from __future__ import annotations

from app.agents.base import AgentOutput
from app.domain.indicators import Candle


def _body(c: Candle) -> float:
    return abs(c.close - c.open)


def _range(c: Candle) -> float:
    return max(c.high - c.low, 1e-9)


def detect_patterns(candles: list[Candle]) -> list[tuple[str, float]]:
    """Retourne une liste de (figure, biais[-1..1]) détectées sur les dernières bougies."""
    if len(candles) < 3:
        return []
    out: list[tuple[str, float]] = []
    prev, last = candles[-2], candles[-1]

    # Avalée (engulfing)
    if last.close > last.open and prev.close < prev.open and last.close >= prev.open and last.open <= prev.close:
        out.append(("avalée haussière", 0.6))
    if last.close < last.open and prev.close > prev.open and last.open >= prev.close and last.close <= prev.open:
        out.append(("avalée baissière", -0.6))

    # Marteau / étoile filante (longue mèche)
    body = _body(last)
    upper = last.high - max(last.close, last.open)
    lower = min(last.close, last.open) - last.low
    if lower > 2 * body and upper < body:
        out.append(("marteau", 0.4))
    if upper > 2 * body and lower < body:
        out.append(("étoile filante", -0.4))

    # Doji (indécision)
    if body < 0.1 * _range(last):
        out.append(("doji", 0.0))

    # Structure : 3 plus hauts/bas croissants
    highs = [c.high for c in candles[-3:]]
    lows = [c.low for c in candles[-3:]]
    if highs[0] < highs[1] < highs[2] and lows[0] < lows[1] < lows[2]:
        out.append(("structure haussière", 0.3))
    if highs[0] > highs[1] > highs[2] and lows[0] > lows[1] > lows[2]:
        out.append(("structure baissière", -0.3))
    return out


async def run(candles: list[Candle], symbol: str = "Symbol", timeframe: str = "TF") -> AgentOutput:
    name = "pattern"
    if len(candles) < 5:
        return AgentOutput(name, 0.0, 0.1, "Données insuffisantes pour l'analyse chartiste.")
    
    patterns = detect_patterns(candles)
    base_score = max(-1.0, min(1.0, sum(b for _, b in patterns) / len(patterns))) if patterns else 0.0
    base_confidence = min(1.0, 0.4 + 0.15 * len(patterns)) if patterns else 0.3
    labels = ", ".join(p for p, _ in patterns) if patterns else "Aucune figure"
    rationale = f"Analyse chartiste (déterministe) : {labels}."

    # Enrichissement Vision LLM (Gemini)
    from app.agents import llm
    if llm.available() and len(candles) >= 10:
        try:
            from app.agents.chart_renderer import render_chart_base64
            img_b64 = render_chart_base64(candles, symbol=symbol, timeframe=timeframe)
            
            prompt = (
                "Analyse ce graphique en chandeliers japonais. "
                "1) Détecte les figures chartistes majeures (supports, résistances, triangles, têtes et épaules, etc.). "
                "2) Donne un biais de marché de -1.0 (très baissier) à 1.0 (très haussier) au format '[Biais: X.X]'. "
                "3) Donne une explication concise. Ne donne pas de conseil financier."
            )
            
            resp = await llm.complete_vision(prompt, img_b64, role="vision", max_tokens=300)
            
            # Extraction du biais si présent
            import re
            from app.agents.base import enrich
            m = re.search(r"\[Biais:\s*(-?\d+\.\d+)\]", resp)
            if m:
                llm_score = float(m.group(1))
                llm_score = max(-1.0, min(1.0, llm_score))
                # Pondération 50/50 entre déterministe et LLM si des figures déterministes existent
                score = (base_score + llm_score) / 2 if patterns else llm_score
                confidence = min(1.0, base_confidence + 0.2)
                # Le commentaire vision s'AJOUTE (sans la balise [Biais]), jamais ne remplace.
                rationale = enrich(rationale, re.sub(r"\[Biais:[^\]]*\]", "", resp).strip())
            else:
                score = base_score
                confidence = base_confidence
                rationale = enrich(rationale, resp.strip())

            return AgentOutput(
                name=name,
                score=round(score, 3),
                confidence=round(confidence, 3),
                rationale=rationale,
                details={"patterns": [p for p, _ in patterns], "vision_used": True},
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Erreur LLM Vision pattern : %s", e)

    return AgentOutput(
        name=name,
        score=round(base_score, 3),
        confidence=round(base_confidence, 3),
        rationale=rationale,
        details={"patterns": [p for p, _ in patterns], "vision_used": False},
    )


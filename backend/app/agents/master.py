"""Master Agent (M2) — orchestration & arbitrage.

Reçoit les sorties des agents spécialisés, détecte les conflits, pondère dynamiquement,
et produit une décision consolidée (direction + score de confiance + justification).
En production : Claude Sonnet pour l'arbitrage ; ici, fusion pondérée déterministe robuste,
enrichie optionnellement par le LLM pour la rédaction.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentOutput
from app.models.signal import Direction

# Poids par défaut des agents (ajustables dynamiquement selon le régime de marché).
DEFAULT_WEIGHTS = {"technical": 0.6, "sentiment": 0.4}


@dataclass
class MasterDecision:
    direction: Direction
    score: float  # -1..+1
    confidence: int  # 0..100
    rationale: str
    conflict: bool


def _weighted(outputs: list[AgentOutput], weights: dict[str, float]) -> float:
    num = 0.0
    den = 0.0
    for o in outputs:
        w = weights.get(o.name, 0.3) * max(o.confidence, 0.05)
        num += w * o.score
        den += w
    return num / den if den else 0.0


def decide(outputs: list[AgentOutput], weights: dict[str, float] | None = None) -> MasterDecision:
    weights = weights or DEFAULT_WEIGHTS
    combined = _weighted(outputs, weights)

    # Détection de conflit : agents pointant dans des directions opposées avec conviction.
    dirs = {o.name: o.direction() for o in outputs}
    has_buy = any(d == Direction.BUY for d in dirs.values())
    has_sell = any(d == Direction.SELL for d in dirs.values())
    conflict = has_buy and has_sell

    if combined > 0.15:
        direction = Direction.BUY
    elif combined < -0.15:
        direction = Direction.SELL
    else:
        direction = Direction.HOLD

    # Confiance : magnitude du score + accord des agents, pénalisée par les conflits.
    agreement = 1.0 - (0.4 if conflict else 0.0)
    confidence = int(round(min(100, abs(combined) * 100 * agreement + 10)))
    if direction == Direction.HOLD:
        confidence = min(confidence, 40)

    parts = [o.rationale for o in outputs]
    arb = "Arbitrage Master : "
    if conflict:
        arb += "signaux divergents détectés, pondération prudente. "
    arb += f"Décision consolidée = {direction.value} (score {combined:+.2f})."
    rationale = arb + " " + " ".join(parts)

    return MasterDecision(
        direction=direction,
        score=round(combined, 3),
        confidence=confidence,
        rationale=rationale,
        conflict=conflict,
    )

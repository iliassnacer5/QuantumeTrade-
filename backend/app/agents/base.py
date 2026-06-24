"""Types partagés pour les agents IA."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.signal import Direction


@dataclass
class AgentOutput:
    """Sortie normalisée d'un agent spécialisé.

    score : biais directionnel dans [-1, +1] (-1 = fortement baissier, +1 = fortement haussier)
    confidence : [0, 1] — confiance de l'agent dans son propre score
    rationale : justification en langage naturel
    """

    name: str
    score: float
    confidence: float
    rationale: str
    details: dict = field(default_factory=dict)

    def direction(self) -> Direction:
        if self.score > 0.15:
            return Direction.BUY
        if self.score < -0.15:
            return Direction.SELL
        return Direction.HOLD

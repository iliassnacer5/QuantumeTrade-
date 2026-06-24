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


def enrich(deterministic: str, llm_text: str | None) -> str:
    """Ajoute un commentaire IA à l'analyse déterministe, SANS jamais la remplacer.

    Garde-fou anti-troncature : on n'ajoute le texte LLM que s'il est complet (se termine par une
    ponctuation de fin de phrase). Un fragment tronqué (modèle « thinking » à court de tokens) est
    ignoré → l'utilisateur voit toujours une analyse cohérente et complète.
    """
    if not llm_text:
        return deterministic
    text = llm_text.strip()
    if len(text) < 15 or text[-1] not in ".!?…":
        return deterministic
    return f"{deterministic} 💬 {text}"

"""Master Agent (M2) — orchestration & arbitrage avec pondération dynamique.

Reçoit les sorties des agents spécialisés, détecte les conflits, pondère dynamiquement (poids de
base × multiplicateurs d'apprentissage du Journal × ajustement selon le régime macro), applique la
contrainte de l'Agent Risque, puis produit une décision consolidée et explicable.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentOutput
from app.models.signal import Direction

# Poids de base par agent.
DEFAULT_WEIGHTS = {
    "technical": 0.25,
    "volume": 0.15,
    "sentiment": 0.20,
    "pattern": 0.15,
    "fundamental": 0.15,
    "macro": 0.10,
}


@dataclass
class MasterDecision:
    direction: Direction
    score: float
    confidence: int
    rationale: str
    conflict: bool
    weights_used: dict


def _effective_weights(
    base: dict[str, float],
    journal_multipliers: dict[str, float] | None,
    regime_bias: float,
) -> dict[str, float]:
    """Combine poids de base, apprentissage (journal) et régime macro."""
    jm = journal_multipliers or {}
    eff = {a: w * jm.get(a, 1.0) for a, w in base.items()}
    # En régime extrême, on accentue le poids macro et on tempère le technique pur.
    if abs(regime_bias) > 0.4:
        eff["macro"] = eff.get("macro", 0.15) * 1.3
        eff["technical"] = eff.get("technical", 0.3) * 0.85
    return eff


def decide(
    outputs: list[AgentOutput],
    *,
    weights: dict[str, float] | None = None,
    journal_multipliers: dict[str, float] | None = None,
    risk_output: AgentOutput | None = None,
) -> MasterDecision:
    base = weights or DEFAULT_WEIGHTS
    regime_bias = next((o.score for o in outputs if o.name == "macro"), 0.0)
    eff = _effective_weights(base, journal_multipliers, regime_bias)

    num = den = 0.0
    for o in outputs:
        if o.name == "risk":  # l'agent risque ne vote pas la direction
            continue
        w = eff.get(o.name, 0.1) * max(o.confidence, 0.05)
        num += w * o.score
        den += w
    combined = num / den if den else 0.0

    dirs = {o.name: o.direction() for o in outputs if o.name != "risk"}
    conflict = any(d == Direction.BUY for d in dirs.values()) and any(
        d == Direction.SELL for d in dirs.values()
    )

    if combined > 0.15:
        direction = Direction.BUY
    elif combined < -0.15:
        direction = Direction.SELL
    else:
        direction = Direction.HOLD

    agreement = 1.0 - (0.4 if conflict else 0.0)
    confidence = abs(combined) * 100 * agreement + 10
    # Contrainte de l'Agent Risque : sa confidence < 1 réduit la confiance globale.
    if risk_output is not None:
        confidence *= max(0.3, risk_output.confidence)
    confidence = int(round(min(100, confidence)))
    if direction == Direction.HOLD:
        confidence = min(confidence, 40)

    parts = [o.rationale for o in outputs]
    arb = "Arbitrage Master : "
    if conflict:
        arb += "signaux divergents, pondération prudente. "
    arb += f"Décision = {direction.value} (score {combined:+.2f})."
    if risk_output is not None and risk_output.details.get("penalty", 0) > 0:
        arb += f" Contrainte risque appliquée (pénalité {risk_output.details['penalty']})."
    rationale = arb + " " + " ".join(parts)

    return MasterDecision(
        direction=direction,
        score=round(combined, 3),
        confidence=confidence,
        rationale=rationale,
        conflict=conflict,
        weights_used={k: round(v, 3) for k, v in eff.items()},
    )

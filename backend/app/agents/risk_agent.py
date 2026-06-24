"""Agent Risque (M2) — contrainte de protection du capital (déterministe, pas de LLM).

Distinct du Risk Engine (M4, qui dimensionne SL/TP) : cet agent évalue le contexte de risque
(exposition courante, drawdown, corrélation) et renvoie une contrainte qui tempère la confiance.
"""

from __future__ import annotations

from app.agents.base import AgentOutput
from app.domain.risk import historical_var


def run_sync(
    *, exposure_pct: float, drawdown_pct: float, correlation: float = 0.0, returns: list[float] | None = None
) -> AgentOutput:
    name = "risk"
    notes: list[str] = []
    penalty = 0.0

    if exposure_pct > 50:
        penalty += 0.4; notes.append(f"exposition élevée {exposure_pct:.0f}%")
    if drawdown_pct > 10:
        penalty += 0.4; notes.append(f"drawdown {drawdown_pct:.0f}%")
    if correlation > 0.8:
        penalty += 0.2; notes.append(f"corrélation portefeuille {correlation:.0%}")
    var = historical_var(returns or [])
    if var > 0.05:
        notes.append(f"VaR95 {var:.1%}")

    # L'agent risque ne donne pas de direction : score 0, mais sa "confidence" représente
    # la fiabilité du contexte ; on expose la pénalité dans les détails pour le Master.
    confidence = max(0.0, 1.0 - penalty)
    rationale = "Contexte de risque : " + ("; ".join(notes) if notes else "nominal") + "."
    return AgentOutput(
        name=name, score=0.0, confidence=round(confidence, 3), rationale=rationale,
        details={"penalty": round(penalty, 3), "var": round(var, 4)},
    )


async def run(**kwargs) -> AgentOutput:
    return run_sync(**kwargs)

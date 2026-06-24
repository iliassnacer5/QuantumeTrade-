"""Service du Journal d'apprentissage (Learning Loop) — 100% synchrone.

Enregistre l'issue des signaux et calcule des multiplicateurs de fiabilité par agent, utilisés par
le Master pour la pondération dynamique. Cohérent avec l'architecture sync (store + repositories).
"""

from __future__ import annotations

import logging

from app.agents.journal import compute_weight_multipliers

logger = logging.getLogger(__name__)


def record_signal(store, tenant_id: str, card, signal_id: str | None = None) -> None:
    """Enregistre un signal généré (issue 'open') avec le détail des scores d'agents."""
    try:
        agent_scores = {a["name"]: a["score"] for a in (getattr(card, "agents", None) or [])}
        store.journal.add(
            tenant_id,
            {
                "signal_id": signal_id,
                "symbol": card.asset,
                "direction": card.direction.value if hasattr(card.direction, "value") else str(card.direction),
                "outcome": "open",
                "pnl": None,
                "agent_scores": agent_scores,
            },
        )
    except Exception as exc:  # noqa: BLE001 — l'apprentissage ne doit jamais casser le flux
        logger.warning("Enregistrement journal échoué (%s)", exc)


def recent_entries(store, tenant_id: str, limit: int = 200) -> list[dict]:
    """Entrées de journal récentes pour `compute_weight_multipliers`."""
    journal_repo = getattr(store, "journal", None)
    if journal_repo is None:
        return []
    try:
        return journal_repo.list_for_tenant(tenant_id, limit)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Lecture journal échouée (%s)", exc)
        return []


def compute_multipliers(store, tenant_id: str) -> dict[str, float]:
    """Multiplicateurs de poids par agent, dérivés de l'historique (taux de réussite)."""
    return compute_weight_multipliers(recent_entries(store, tenant_id))

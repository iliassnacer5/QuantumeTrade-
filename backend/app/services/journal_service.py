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


def close_trade(store, tenant_id: str, entry_id: str, outcome: str, pnl: float | None) -> dict | None:
    """Enregistre l'issue d'un trade (win/loss/breakeven) — alimente la boucle d'apprentissage."""
    if outcome not in {"win", "loss", "breakeven", "open"}:
        raise ValueError("issue invalide")
    return store.journal.update_outcome(tenant_id, entry_id, outcome=outcome, pnl=pnl)


def stats(entries: list[dict]) -> dict:
    """KPI agrégés du journal (trades clôturés)."""
    closed = [e for e in entries if e.get("outcome") in {"win", "loss", "breakeven"}]
    wins = [e for e in closed if e.get("outcome") == "win"]
    losses = [e for e in closed if e.get("outcome") == "loss"]
    total_pnl = sum(float(e.get("pnl") or 0.0) for e in closed)
    n = len(closed)
    return {
        "total_entries": len(entries),
        "closed": n,
        "open": len([e for e in entries if e.get("outcome") == "open"]),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / n * 100, 1) if n else 0.0,
        "total_pnl": round(total_pnl, 2),
    }


async def explain_trade(entry: dict) -> str:
    """Explication IA d'un trade (post-mortem) + analyse des erreurs ; repli déterministe sans LLM."""
    from app.agents import llm

    scores = entry.get("agent_scores") or {}
    drivers = ", ".join(f"{k} ({v:+.2f})" for k, v in scores.items()) or "aucun score d'agent"
    outcome = entry.get("outcome", "open")
    base = (
        f"Trade {entry.get('direction')} sur {entry.get('symbol')} — issue : {outcome}, "
        f"P&L : {entry.get('pnl')}. Moteurs au moment du signal : {drivers}."
    )
    if not llm.available():
        verdict = {
            "win": "Les agents alignés sur la direction ont été confirmés par le marché.",
            "loss": "Le marché a invalidé le biais : revoir la pondération des agents divergents.",
            "breakeven": "Issue neutre : la conviction des agents était probablement faible.",
            "open": "Trade encore ouvert : pas d'analyse post-mortem disponible.",
        }.get(outcome, "")
        return f"{base}\n{verdict}\n(Analyse déterministe — configurez une clé LLM pour un post-mortem détaillé.)"
    try:
        prompt = (
            "Tu es un coach de trading. Analyse ce trade de façon concise (3-4 phrases) : "
            "qu'est-ce qui a fonctionné ou non, et quelle leçon en tirer pour les pondérations d'agents. "
            f"Ne donne pas de conseil financier.\n\nDONNÉES : {base}"
        )
        return (await llm.complete(prompt, role="reasoning", max_tokens=300)).strip()
    except llm.LLMUnavailable:
        return base

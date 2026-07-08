"""Agent Journal (M2) — mémoire & apprentissage.

À partir de l'historique des signaux et de leur issue (gagnant/perdant), calcule un multiplicateur
de fiabilité par agent : un agent dont les appels directionnels se sont avérés justes voit son poids
augmenter, et inversement.

Apprentissage proportionnel au VOLUME de données (clé de la demande « apprend au fur et à mesure
avec beaucoup de trades ») : avec peu d'exemples, on reste prudent (proche de la neutralité) ; plus
les trades s'accumulent, plus l'ajustement devient marqué et fiable. Facteur de confiance bayésien
``n / (n + K)`` : on ne sur-réagit pas à 3 trades, mais on exploite pleinement 100 trades.
"""

from __future__ import annotations

# Lissage : nombre de trades à partir duquel on « fait à moitié confiance » au taux observé.
_CONFIDENCE_K = 12
# Amplitude maximale de l'ajustement (à confiance pleine) : 100% de réussite -> 1.5, 0% -> 0.5.
_MAX_SWING = 0.5


def compute_weight_multipliers(entries: list[dict]) -> dict[str, float]:
    """entries: [{outcome: 'win'|'loss', agent_scores: {agent: score}, direction: 'BUY'|'SELL'}].

    Retourne {agent: multiplicateur in [0.5, 1.5]} basé sur le taux de réussite directionnelle,
    pondéré par le volume de données (plus de trades -> ajustement plus marqué et plus fiable).
    """
    hits: dict[str, int] = {}
    total: dict[str, int] = {}
    for e in entries:
        outcome = e.get("outcome")
        if outcome not in ("win", "loss"):
            continue
        direction = e.get("direction")
        for agent, score in (e.get("agent_scores") or {}).items():
            agent_dir = "BUY" if score > 0.15 else "SELL" if score < -0.15 else None
            if agent_dir is None:
                continue
            total[agent] = total.get(agent, 0) + 1
            agreed = agent_dir == direction
            correct = (agreed and outcome == "win") or (not agreed and outcome == "loss")
            if correct:
                hits[agent] = hits.get(agent, 0) + 1

    multipliers: dict[str, float] = {}
    for agent, n in total.items():
        if n < 3:  # trop peu de données -> neutre
            multipliers[agent] = 1.0
            continue
        hit_rate = hits.get(agent, 0) / n
        confidence = n / (n + _CONFIDENCE_K)  # 0 -> ... -> 1 quand n grandit
        # Écart au hasard (50%) amplifié par la confiance : peu de données = ajustement timide.
        adjustment = (hit_rate - 0.5) * 2 * _MAX_SWING * confidence
        multipliers[agent] = round(min(1.5, max(0.5, 1.0 + adjustment)), 3)
    return multipliers


def reliability_report(entries: list[dict]) -> list[dict]:
    """Détail par agent pour l'UI : taux de réussite, volume appris, multiplicateur courant."""
    hits: dict[str, int] = {}
    total: dict[str, int] = {}
    for e in entries:
        if e.get("outcome") not in ("win", "loss"):
            continue
        direction = e.get("direction")
        for agent, score in (e.get("agent_scores") or {}).items():
            agent_dir = "BUY" if score > 0.15 else "SELL" if score < -0.15 else None
            if agent_dir is None:
                continue
            total[agent] = total.get(agent, 0) + 1
            agreed = agent_dir == direction
            if (agreed and e["outcome"] == "win") or (not agreed and e["outcome"] == "loss"):
                hits[agent] = hits.get(agent, 0) + 1

    mults = compute_weight_multipliers(entries)
    return sorted(
        [
            {
                "agent": a,
                "samples": n,
                "hit_rate": round(hits.get(a, 0) / n * 100, 1) if n else 0.0,
                "multiplier": mults.get(a, 1.0),
                # < 10 appels directionnels = bruit statistique (un "0%" sur n=8 n'est pas fiable).
                "low_sample": n < 10,
            }
            for a, n in total.items()
        ],
        key=lambda r: r["multiplier"],
        reverse=True,
    )

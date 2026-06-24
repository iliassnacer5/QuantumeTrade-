"""Agent Journal (M2) — mémoire & apprentissage.

À partir de l'historique des signaux et de leur issue (gagnant/perdant), calcule un multiplicateur
de fiabilité par agent : un agent dont les appels directionnels se sont avérés justes voit son poids
augmenter, et inversement. Boucle d'amélioration continue, déterministe.
"""

from __future__ import annotations


def compute_weight_multipliers(entries: list[dict]) -> dict[str, float]:
    """entries: [{outcome: 'win'|'loss', agent_scores: {agent: score}, direction: 'BUY'|'SELL'}].

    Retourne {agent: multiplicateur in [0.5, 1.5]} basé sur le taux de réussite directionnelle.
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
        if n < 3:  # pas assez de données -> neutre
            multipliers[agent] = 1.0
            continue
        hit_rate = hits.get(agent, 0) / n
        # 50% -> 1.0 ; 100% -> 1.5 ; 0% -> 0.5
        multipliers[agent] = round(0.5 + hit_rate, 3)
    return multipliers

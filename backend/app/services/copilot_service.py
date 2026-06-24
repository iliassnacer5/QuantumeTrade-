"""AI Copilot (M5) — service conversationnel contextuel — Phase 3.

Construit un contexte riche (données marché récentes + sorties des agents + portefeuille) puis
interroge le LLM (rôle 'reasoning' = Claude/Gemini selon clés) en streaming. Sans LLM, renvoie une
synthèse déterministe à partir des agents : le Copilot reste utile hors-ligne.
"""

from __future__ import annotations

import logging

from app.agents import llm
from app.domain import indicators as ind
from app.models.entities import User
from app.models.signal import Timeframe
from app.repositories.store import AppStore
from app.services import signal_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Tu es l'AI Copilot de Quantum Trade AI, un assistant de trading factuel et prudent. "
    "Tu expliques l'analyse multi-agents (technique, volume, sentiment, figures, macro, risque) "
    "de façon claire et pédagogique, en français. Tu ne donnes JAMAIS de conseil financier "
    "personnalisé ni de garantie de gain ; tu rappelles les risques. Tu t'appuies uniquement sur "
    "le CONTEXTE fourni (données marché et sorties d'agents)."
)


async def build_context(user: User, store: AppStore, asset: str) -> dict:
    """Génère un instantané d'analyse pour `asset` (réutilise le pipeline de signaux, sans notif)."""
    card = await signal_service.generate_for_user(
        user, store, asset=asset, timeframe=Timeframe.SWING, notify=False
    )
    candles = await signal_service._load_candles(asset, Timeframe.SWING)
    last = candles[-1].close if candles else 0.0
    rsi = ind.rsi([c.close for c in candles], 14) if len(candles) > 14 else None
    return {
        "asset": asset,
        "last_price": round(last, 8),
        "rsi": round(rsi, 1) if rsi is not None else None,
        "signal": {
            "direction": card.direction.value,
            "confidence": card.confidence,
            "entry": card.entry,
            "stop_loss": card.stop_loss,
            "take_profit_1": card.take_profit_1,
            "rationale": card.rationale,
        },
        "agents": [
            {"name": a["name"], "score": a["score"], "confidence": a["confidence"], "rationale": a["rationale"]}
            for a in (card.agents or [])
        ],
    }


def _context_text(ctx: dict) -> str:
    lines = [
        f"Actif : {ctx['asset']} | Dernier prix : {ctx['last_price']} | RSI(14) : {ctx['rsi']}",
        f"Signal consolidé : {ctx['signal']['direction']} (confiance {ctx['signal']['confidence']}%) — "
        f"entrée {ctx['signal']['entry']}, stop {ctx['signal']['stop_loss']}, TP1 {ctx['signal']['take_profit_1']}",
        f"Justification : {ctx['signal']['rationale']}",
        "Détail des agents :",
    ]
    for a in ctx["agents"]:
        lines.append(f"  - {a['name']} : score {a['score']:+.2f}, conf {a['confidence']:.2f} — {a['rationale']}")
    return "\n".join(lines)


def _deterministic_answer(question: str, ctx: dict) -> str:
    """Réponse de repli (sans LLM) : synthèse structurée du contexte."""
    s = ctx["signal"]
    top = sorted(ctx["agents"], key=lambda a: abs(a["score"]), reverse=True)[:3]
    drivers = ", ".join(f"{a['name']} ({a['score']:+.2f})" for a in top) or "aucun signal marqué"
    return (
        f"Analyse de {ctx['asset']} (prix {ctx['last_price']}, RSI {ctx['rsi']}).\n"
        f"Biais consolidé : {s['direction']} avec une confiance de {s['confidence']}%.\n"
        f"Principaux moteurs : {drivers}.\n"
        f"Niveaux : entrée {s['entry']}, stop {s['stop_loss']}, objectif {s['take_profit_1']}.\n"
        f"Rappel : ceci est une analyse automatisée, pas un conseil financier. "
        f"(Copilot en mode déterministe — configurez une clé LLM pour des réponses conversationnelles.)"
    )


async def answer_stream(user: User, store: AppStore, asset: str, question: str):
    """Async generator de fragments de texte (pour SSE). Inclut un repli déterministe."""
    ctx = await build_context(user, store, asset)
    prompt = (
        f"CONTEXTE D'ANALYSE :\n{_context_text(ctx)}\n\n"
        f"QUESTION DE L'UTILISATEUR : {question}\n\n"
        f"Réponds de façon concise et structurée en t'appuyant sur le contexte."
    )
    if not llm.available():
        yield _deterministic_answer(question, ctx)
        return
    try:
        async for piece in llm.stream(prompt, role="reasoning", system=SYSTEM_PROMPT, max_tokens=800):
            yield piece
    except llm.LLMUnavailable:
        yield _deterministic_answer(question, ctx)

"""Abstraction LLM multi-fournisseurs (LiteLLM) avec fallback déterministe.

- Si une clé API est configurée -> route via LiteLLM (Claude/Gemini selon l'agent).
- Sinon -> fallback : renvoie une explication construite par template (mode offline/MVP/tests).

Ce découplage garantit que le système produit toujours des signaux, même sans LLM,
et permet le failover entre fournisseurs (cf. cahier des charges §3.4).
"""

from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def llm_available() -> bool:
    s = get_settings()
    return bool(s.anthropic_api_key or s.google_api_key)


async def complete(prompt: str, *, model: str | None = None, max_tokens: int = 512) -> str:
    """Complétion texte. Tente LiteLLM si dispo, sinon lève pour laisser l'appelant utiliser son fallback."""
    s = get_settings()
    if not llm_available():
        raise RuntimeError("Aucune clé LLM configurée — utiliser le fallback déterministe")
    try:
        import litellm  # import paresseux : dépendance optionnelle

        resp = await litellm.acompletion(
            model=model or s.litellm_default_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return resp["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001 — on log et on bascule en fallback
        logger.warning("LLM indisponible (%s), fallback déterministe", exc)
        raise

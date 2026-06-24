"""Routeur LLM multi-fournisseurs (LiteLLM) — stratégie hybride Claude/Gemini.

- Sélectionne le modèle selon le *rôle* de l'agent (master, fast, vision, grounding, reasoning).
- Failover automatique : si le fournisseur primaire est indisponible (clé absente ou erreur),
  bascule vers l'autre fournisseur ; si rien n'est disponible -> lève `LLMUnavailable` pour que
  l'agent utilise son fallback déterministe.
- Supporte le texte et la vision (image base64) pour l'Agent Pattern.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LLMUnavailable(RuntimeError):
    """Aucun fournisseur LLM disponible pour ce rôle."""


def _provider_of(model: str) -> str:
    m = model.lower()
    if m.startswith("gemini/") or m.startswith("google") or "gemini" in m:
        return "google"
    if "claude" in m or m.startswith("anthropic"):
        return "anthropic"
    return "unknown"


def _has_key(provider: str) -> bool:
    s = get_settings()
    return {"google": bool(s.google_api_key), "anthropic": bool(s.anthropic_api_key)}.get(provider, False)


def _api_key_for(provider: str) -> str | None:
    s = get_settings()
    return {"google": s.google_api_key, "anthropic": s.anthropic_api_key}.get(provider)


def _models_for_role(role: str) -> list[str]:
    """Chaîne de failover ordonnée pour un rôle (primaire puis secours)."""
    s = get_settings()
    primary = {
        "master": s.llm_model_master,
        "reasoning": s.llm_model_reasoning,
        "fast": s.llm_model_fast,
        "vision": s.llm_model_vision,
        "grounding": s.llm_model_grounding,
    }.get(role, s.litellm_default_model)
    # Secours = l'autre fournisseur (modèle par défaut opposé).
    fallback = s.llm_model_fast if _provider_of(primary) == "anthropic" else s.llm_model_master
    chain = [primary, fallback]
    # On ne garde que les modèles dont la clé est disponible (en préservant l'ordre).
    return [m for m in dict.fromkeys(chain) if _has_key(_provider_of(m))]


def available() -> bool:
    s = get_settings()
    return s.llm_enabled and (bool(s.anthropic_api_key) or bool(s.google_api_key))


def route(role: str) -> str | None:
    """Retourne le modèle qui serait utilisé pour ce rôle (ou None)."""
    chain = _models_for_role(role)
    return chain[0] if chain else None


async def _acompletion(model: str, messages: list[dict], api_key: str | None, max_tokens: int) -> str:
    """Appel LiteLLM réel (séparé pour faciliter le mock en test)."""
    import litellm

    resp = await litellm.acompletion(
        model=model, messages=messages, api_key=api_key, max_tokens=max_tokens
    )
    content = resp["choices"][0]["message"]["content"]
    # Les modèles "thinking" (ex. gemini-2.5-pro) peuvent renvoyer content=None (réponse vide ou
    # tronquée par les tokens de raisonnement). On lève pour déclencher le failover/fallback.
    if not content or not content.strip():
        raise RuntimeError("réponse LLM vide (content=None)")
    return content


async def complete(prompt: str, *, role: str = "reasoning", max_tokens: int = 512) -> str:
    """Complétion texte avec failover. Lève LLMUnavailable si aucun fournisseur."""
    if not get_settings().llm_enabled:
        raise LLMUnavailable("LLM désactivé")
    chain = _models_for_role(role)
    if not chain:
        raise LLMUnavailable(f"Aucun modèle disponible pour le rôle '{role}'")
    messages = [{"role": "user", "content": prompt}]
    last_exc: Exception | None = None
    for model in chain:
        try:
            return await _acompletion(model, messages, _api_key_for(_provider_of(model)), max_tokens)
        except Exception as exc:  # noqa: BLE001 — failover
            logger.warning("LLM %s indisponible (%s), tentative suivante", model, exc)
            last_exc = exc
    raise LLMUnavailable(f"Échec de tous les fournisseurs pour '{role}': {last_exc}")


async def stream(prompt: str, *, role: str = "reasoning", max_tokens: int = 1024, system: str | None = None):
    """Génère la réponse en streaming (tokens). Yield des fragments de texte.

    Utilisé par l'AI Copilot (Phase 3). Lève `LLMUnavailable` si aucun fournisseur ; l'appelant
    bascule alors sur une réponse déterministe.
    """
    if not get_settings().llm_enabled:
        raise LLMUnavailable("LLM désactivé")
    chain = _models_for_role(role)
    if not chain:
        raise LLMUnavailable(f"Aucun modèle disponible pour le rôle '{role}'")
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_exc: Exception | None = None
    for model in chain:
        try:
            import litellm

            resp = await litellm.acompletion(
                model=model,
                messages=messages,
                api_key=_api_key_for(_provider_of(model)),
                max_tokens=max_tokens,
                stream=True,
            )
            produced = False
            async for chunk in resp:
                delta = (chunk.get("choices") or [{}])[0].get("delta") or {}
                piece = delta.get("content")
                if piece:
                    produced = True
                    yield piece
            if produced:
                return
            raise RuntimeError("flux LLM vide")
        except Exception as exc:  # noqa: BLE001 — failover
            logger.warning("LLM stream %s indisponible (%s), tentative suivante", model, exc)
            last_exc = exc
    raise LLMUnavailable(f"Échec stream pour '{role}': {last_exc}")


async def complete_vision(prompt: str, image_b64: str, *, role: str = "vision", max_tokens: int = 512) -> str:
    """Complétion multimodale (image) pour l'Agent Pattern."""
    if not get_settings().llm_enabled:
        raise LLMUnavailable("LLM désactivé")
    chain = _models_for_role(role)
    if not chain:
        raise LLMUnavailable("Aucun modèle vision disponible")
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            ],
        }
    ]
    last_exc: Exception | None = None
    for model in chain:
        try:
            return await _acompletion(model, messages, _api_key_for(_provider_of(model)), max_tokens)
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM vision %s indisponible (%s)", model, exc)
            last_exc = exc
    raise LLMUnavailable(f"Échec vision: {last_exc}")


# Rétrocompat : ancien nom utilisé ailleurs.
def llm_available() -> bool:
    return available()

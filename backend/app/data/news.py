"""Connecteur news / sentiment (M1).

Récupère les actualités d'un actif via Finnhub (si clé configurée), sinon renvoie une liste vide
(l'Agent Sentiment gère gracieusement l'absence de news).
"""

from __future__ import annotations

import logging

from app.agents.sentiment import NewsItem
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def fetch_news(symbol: str, limit: int = 20) -> list[NewsItem]:
    """Récupère les dernières news. Retourne [] si pas de clé ou en cas d'erreur."""
    s = get_settings()
    api_key = getattr(s, "finnhub_api_key", "") or ""
    if not api_key:
        return []
    try:
        import httpx

        base = symbol.split("/")[0]
        url = "https://finnhub.io/api/v1/company-news"
        params = {"symbol": base, "token": api_key}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()[:limit]
        return [NewsItem(headline=item.get("headline", "")) for item in data if item.get("headline")]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Récupération news échouée (%s)", exc)
        return []

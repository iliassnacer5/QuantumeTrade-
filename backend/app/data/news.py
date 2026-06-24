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
    """Récupère les dernières news (CryptoPanic pour crypto, Finnhub pour actions)."""
    s = get_settings()
    news = []
    import httpx
    
    # Tentative CryptoPanic (si crypto)
    if "BTC" in symbol or "ETH" in symbol or "SOL" in symbol or "USDT" in symbol:
        # CryptoPanic API doesn't require a key for public endpoints, but auth_token is better.
        # We will try a public alternative or just use finnhub if no panic key.
        pass # To be implemented fully when auth token is provided. 
        # For now, let's keep the structure ready.
        # cryptopanic_url = "https://cryptopanic.com/api/v1/posts/?filter=important"

    # Tentative Finnhub
    api_key = getattr(s, "finnhub_api_key", "") or ""
    if api_key:
        try:
            base = symbol.split("/")[0].split("-")[0]
            url = "https://finnhub.io/api/v1/company-news"
            params = {"symbol": base, "token": api_key}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()[:limit]
            news.extend([NewsItem(headline=item.get("headline", "")) for item in data if item.get("headline")])
        except Exception as exc:
            logger.warning("Récupération news Finnhub échouée (%s)", exc)
            
    return news


async def fetch_fear_greed() -> int | None:
    """Récupère l'index Fear & Greed crypto."""
    try:
        import httpx
        url = "https://api.alternative.me/fng/"
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return int(data["data"][0]["value"])
    except Exception as exc:
        logger.warning("Récupération Fear & Greed échouée (%s)", exc)
        return None

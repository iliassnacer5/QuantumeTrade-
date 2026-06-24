"""Connecteur news / sentiment multi-fournisseurs (M1 + amélioration).

Récupère de vraies actualités financières selon la classe d'actif (crypto / forex / actions) via,
dans l'ordre de disponibilité : newsdata.io, NewsAPI.org, Finnhub. Dégrade gracieusement vers une
liste vide (l'Agent Sentiment bascule alors sur l'indice de marché momentum).
"""

from __future__ import annotations

import logging

from app.agents.sentiment import NewsItem
from app.core.config import get_settings
from app.data import markets

logger = logging.getLogger(__name__)

# Noms lisibles pour la recherche de news par devise/crypto.
_CRYPTO_NAMES = {
    "BTC": "Bitcoin", "ETH": "Ethereum", "SOL": "Solana", "XRP": "XRP", "ADA": "Cardano",
    "DOGE": "Dogecoin", "BNB": "Binance Coin", "AVAX": "Avalanche", "MATIC": "Polygon", "DOT": "Polkadot",
}
_FX_NAMES = {
    "EUR": "euro", "USD": "dollar", "GBP": "pound", "JPY": "yen", "CHF": "franc",
    "AUD": "Australian dollar", "CAD": "Canadian dollar", "NZD": "New Zealand dollar",
}


def _query_for(symbol: str) -> str:
    """Construit une requête de recherche pertinente selon la classe d'actif."""
    cls = markets.asset_class(symbol)
    if cls == "crypto":
        base = symbol.split("/")[0].split("-")[0].upper()
        return _CRYPTO_NAMES.get(base, base) + " crypto"
    if cls == "forex":
        base, quote = (symbol.split("/") + [""])[:2]
        return f"{_FX_NAMES.get(base.upper(), base)} {_FX_NAMES.get(quote.upper(), quote)} forex"
    # actions : le ticker tel quel (AAPL, TSLA…)
    return symbol.split("/")[0].split("-")[0].upper()


async def _newsdata(query: str, limit: int) -> list[NewsItem]:
    s = get_settings()
    if not s.newsdata_key:
        return []
    import httpx

    url = "https://newsdata.io/api/1/latest"
    params = {"apikey": s.newsdata_key, "q": query, "language": "en"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        results = resp.json().get("results", []) or []
    return [NewsItem(headline=a.get("title", "")) for a in results[:limit] if a.get("title")]


async def _newsapi(query: str, limit: int) -> list[NewsItem]:
    s = get_settings()
    if not s.newsapi_key:
        return []
    import httpx

    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "apiKey": s.newsapi_key, "language": "en", "sortBy": "publishedAt", "pageSize": limit}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        articles = resp.json().get("articles", []) or []
    return [NewsItem(headline=a.get("title", "")) for a in articles[:limit] if a.get("title")]


async def _finnhub(symbol: str, limit: int) -> list[NewsItem]:
    s = get_settings()
    if not s.finnhub_api_key:
        return []
    import httpx

    base = symbol.split("/")[0].split("-")[0].upper()
    url = "https://finnhub.io/api/v1/company-news"
    params = {"symbol": base, "token": s.finnhub_api_key, "from": "2024-01-01", "to": "2030-01-01"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()[:limit]
    return [NewsItem(headline=i.get("headline", "")) for i in data if i.get("headline")]


async def fetch_news(symbol: str, limit: int = 20) -> list[NewsItem]:
    """Récupère de vraies news via le 1er fournisseur disponible (newsdata.io > NewsAPI > Finnhub)."""
    query = _query_for(symbol)
    # NewsAPI en premier (rapide/fiable), puis newsdata.io, puis Finnhub.
    for provider, coro in (
        ("NewsAPI", _newsapi(query, limit)),
        ("newsdata.io", _newsdata(query, limit)),
        ("Finnhub", _finnhub(symbol, limit)),
    ):
        try:
            items = await coro
            if items:
                logger.info("News %s via %s : %d titres", symbol, provider, len(items))
                return items
        except Exception as exc:  # noqa: BLE001 — on tente le fournisseur suivant
            logger.warning("News %s via %s échoué (%s: %s)", symbol, provider, type(exc).__name__, exc)
    return []


async def fetch_fear_greed() -> int | None:
    """Récupère l'index Fear & Greed crypto (alternative.me, sans clé)."""
    try:
        import httpx

        url = "https://api.alternative.me/fng/"
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return int(resp.json()["data"][0]["value"])
    except Exception as exc:  # noqa: BLE001
        logger.warning("Récupération Fear & Greed échouée (%s)", exc)
        return None

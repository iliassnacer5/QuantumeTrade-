"""Connecteur de ratios fondamentaux (actions) — via Finnhub `/stock/metric`.

Alimente l'Agent Fondamental avec de vrais ratios (PER, croissance du CA, dette/capitaux, marge
nette). Sans clé Finnhub ou hors actions, renvoie None (l'agent reste alors neutre).
"""

from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def fetch_ratios(symbol: str) -> dict | None:
    """Récupère les ratios fondamentaux d'une action ; None si indisponible."""
    s = get_settings()
    if not s.finnhub_api_key:
        return None
    base = symbol.split("/")[0].split("-")[0].upper()
    try:
        import httpx

        url = "https://finnhub.io/api/v1/stock/metric"
        params = {"symbol": base, "metric": "all", "token": s.finnhub_api_key}
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            m = (resp.json() or {}).get("metric", {}) or {}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Fondamentaux %s indisponibles (%s)", base, exc)
        return None

    ratios: dict = {}
    pe = m.get("peTTM") or m.get("peBasicExclExtraTTM")
    if pe is not None:
        ratios["pe"] = pe
    rg = m.get("revenueGrowthTTMYoy")
    if rg is not None:
        ratios["revenue_growth"] = rg / 100.0  # Finnhub en %, l'agent attend une fraction
    de = m.get("totalDebt/totalEquityQuarterly")
    if de is None:
        de = m.get("longTermDebt/equityQuarterly")
    if de is not None:
        ratios["debt_to_equity"] = de
    nm = m.get("netProfitMarginTTM")
    if nm is not None:
        ratios["net_margin"] = nm / 100.0
    return ratios or None

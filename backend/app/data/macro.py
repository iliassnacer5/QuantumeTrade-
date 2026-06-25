"""Connecteur de données Macro (FRED - Federal Reserve Economic Data)."""

from __future__ import annotations

import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)

async def fetch_macro_data() -> dict:
    """
    Récupère les indicateurs macro-économiques.
    Retourne un dictionnaire avec rate_trend, inflation, vix.
    """
    s = get_settings()
    api_key = getattr(s, "fred_api_key", "") or ""

    macro = {"rate_trend": "flat", "inflation": None, "vix": None}

    if api_key:
        await _fetch_fred(macro, api_key)

    # Repli VIX via Yahoo (gratuit, sans clé) — indicateur clé du régime risk-on/risk-off.
    if macro["vix"] is None:
        try:
            from app.data import yahoo

            rows = await yahoo.fetch_ohlcv("^VIX", "1d", limit=2)
            if rows:
                macro["vix"] = round(rows[-1]["close"], 2)
        except Exception as exc:  # noqa: BLE001
            logger.warning("VIX Yahoo indisponible (%s)", exc)

    return macro


async def _fetch_fred(macro: dict, api_key: str) -> None:
    """Remplit taux/inflation/VIX depuis FRED (clé requise)."""
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=10) as client:
            # 1. Fed Funds Rate (DFF)
            fed_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DFF&api_key={api_key}&file_type=json&limit=2&sort_order=desc"
            fed_resp = await client.get(fed_url)
            fed_resp.raise_for_status()
            fed_data = fed_resp.json().get("observations", [])
            if len(fed_data) >= 2:
                curr_rate = float(fed_data[0]["value"])
                prev_rate = float(fed_data[1]["value"])
                if curr_rate > prev_rate:
                    macro["rate_trend"] = "up"
                elif curr_rate < prev_rate:
                    macro["rate_trend"] = "down"
            
            # 2. Inflation (CPIAUCSL YoY)
            cpi_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL&api_key={api_key}&file_type=json&limit=13&sort_order=desc"
            cpi_resp = await client.get(cpi_url)
            cpi_resp.raise_for_status()
            cpi_data = cpi_resp.json().get("observations", [])
            if len(cpi_data) >= 13:
                curr_cpi = float(cpi_data[0]["value"])
                prev_yr_cpi = float(cpi_data[12]["value"])
                macro["inflation"] = round((curr_cpi - prev_yr_cpi) / prev_yr_cpi * 100, 2)
            
            # 3. VIX (VIXCLS)
            vix_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=VIXCLS&api_key={api_key}&file_type=json&limit=1&sort_order=desc"
            vix_resp = await client.get(vix_url)
            vix_resp.raise_for_status()
            vix_data = vix_resp.json().get("observations", [])
            if vix_data and vix_data[0]["value"] != ".":
                macro["vix"] = float(vix_data[0]["value"])

    except Exception as exc:  # noqa: BLE001
        logger.warning("Récupération données FRED échouée (%s)", exc)

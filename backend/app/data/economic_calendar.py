"""Filtre événementiel — bloque les signaux autour des événements à fort impact (Phase 1).

- Actions : earnings via Finnhub (blackout 48h avant / 24h après).
- Crypto / forex : fenêtre autour des dates FOMC configurables (blackout court).
Repli GRACIEUX : toute indisponibilité => pas de blackout (on ne bloque jamais par erreur réseau).
Le scraping Forex Factory (news macro génériques) est reporté en Phase 2 (fragile/bloqué).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, date, datetime, timedelta

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_earnings_cache: dict[str, tuple[float, str | None]] = {}


def _fomc_dates() -> list[date]:
    raw = get_settings().fomc_dates or ""
    out: list[date] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            out.append(datetime.fromisoformat(token).date())
        except ValueError:
            continue
    return out


def _in_fomc_window(now: datetime) -> bool:
    """Fenêtre FOMC : la veille au soir jusqu'au lendemain (impact macro fort sur crypto/forex)."""
    today = now.date()
    for d in _fomc_dates():
        if abs((today - d).days) <= 1:
            return True
    return False


async def _earnings_date(symbol: str) -> str | None:
    """Prochaine date d'earnings (ISO) via Finnhub, mise en cache 6h. None si indisponible."""
    s = get_settings()
    if not s.finnhub_api_key:
        return None
    base = symbol.split("/")[0].split("-")[0].upper()
    item = _earnings_cache.get(base)
    if item and item[0] > time.time():
        return item[1]
    result: str | None = None
    try:
        import httpx

        today = datetime.now(UTC).date()
        url = "https://finnhub.io/api/v1/calendar/earnings"
        params = {"symbol": base, "from": today.isoformat(),
                  "to": (today + timedelta(days=5)).isoformat(), "token": s.finnhub_api_key}
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            rows = (resp.json() or {}).get("earningsCalendar", []) or []
        result = rows[0].get("date") if rows else None
    except Exception as exc:  # noqa: BLE001 — repli gracieux
        logger.warning("Earnings %s indisponibles (%s)", base, exc)
    _earnings_cache[base] = (time.time() + 6 * 3600, result)
    return result


async def is_news_blackout(symbol: str, market_type: str) -> tuple[bool, str]:
    """Retourne (blackout, raison). Repli gracieux -> (False, "")."""
    if not get_settings().event_blackout_enabled:
        return False, ""
    now = datetime.now(UTC)
    try:
        if market_type == "stock":
            iso = await _earnings_date(symbol)
            if iso:
                try:
                    ed = datetime.fromisoformat(iso).date()
                    delta = (ed - now.date()).days
                    if -1 <= delta <= 2:  # 48h avant / 24h après
                        return True, f"earnings {symbol.split('/')[0]} le {iso}"
                except ValueError:
                    pass
        else:  # crypto / forex
            if _in_fomc_window(now):
                return True, "fenêtre FOMC (volatilité macro)"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Calendrier économique %s indisponible (%s)", symbol, exc)
    return False, ""

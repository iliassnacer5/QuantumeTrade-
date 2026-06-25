"""Sessions de trading mondiales (Asie / Londres / New York).

Chaque session a sa fenêtre horaire (UTC) et ses actifs les plus liquides — donc les plus fiables à
trader pendant cette session. La crypto est 24/7 (toujours incluse) ; le forex et les actions sont
filtrés selon la session active. Permet de scanner « les bonnes paires au bon moment ».
"""

from __future__ import annotations

from datetime import datetime, timezone

# Cryptos majeures — liquides en continu, incluses dans toutes les sessions.
_CRYPTO = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT"]

SESSIONS: dict[str, dict] = {
    "asian": {
        "label": "Asie (Tokyo/Sydney)",
        "start": 23, "end": 8,  # UTC (chevauche minuit)
        "forex": ["USD/JPY", "EUR/JPY", "GBP/JPY", "AUD/JPY", "AUD/USD", "NZD/USD"],
        "stocks": [],  # marchés US/EU fermés
    },
    "london": {
        "label": "Londres (Europe)",
        "start": 7, "end": 16,
        "forex": ["EUR/USD", "GBP/USD", "EUR/GBP", "EUR/CHF", "GBP/CHF", "USD/CHF", "EUR/JPY"],
        "stocks": [],  # actions EU non couvertes ; US en pré-marché
    },
    "newyork": {
        "label": "New York (Amérique)",
        "start": 12, "end": 21,
        "forex": ["EUR/USD", "GBP/USD", "USD/CAD", "USD/JPY", "USD/CHF"],
        "stocks": ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "AMD", "NFLX", "JPM"],
    },
}


def _is_open(start: int, end: int, hour: int) -> bool:
    return start <= hour < end if start <= end else (hour >= start or hour < end)


def current_sessions(now: datetime | None = None) -> list[str]:
    """Sessions actuellement ouvertes (elles se chevauchent)."""
    h = (now or datetime.now(timezone.utc)).hour
    return [name for name, s in SESSIONS.items() if _is_open(s["start"], s["end"], h)]


def session_universe(session: str) -> list[dict]:
    """Actifs pertinents pour une session : crypto (toujours) + forex + actions de la session."""
    s = SESSIONS.get(session)
    if not s:
        return []
    out = [{"symbol": c, "asset_class": "crypto"} for c in _CRYPTO]
    out += [{"symbol": f, "asset_class": "forex"} for f in s["forex"]]
    out += [{"symbol": a, "asset_class": "stock"} for a in s["stocks"]]
    return out


def overview(now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    active = current_sessions(now)
    return {
        "utc_time": now.strftime("%H:%M UTC"),
        "active": active,
        "sessions": [
            {
                "id": name,
                "label": s["label"],
                "window_utc": f"{s['start']:02d}:00–{s['end']:02d}:00",
                "open": name in active,
                "symbol_count": len(session_universe(name)),
            }
            for name, s in SESSIONS.items()
        ],
    }

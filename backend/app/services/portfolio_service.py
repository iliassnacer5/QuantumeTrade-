"""Calcul du P&L latent du portefeuille (Lot 3).

Les positions sont dérivées des signaux non-HOLD de l'utilisateur. Le P&L latent est estimé à
partir du dernier prix de marché. Déterministe.
"""

from __future__ import annotations

from app.data.ohlcv import get_ohlcv
from app.models.entities import User
from app.repositories.store import AppStore


async def _last_price(symbol: str) -> float | None:
    data = await get_ohlcv(symbol, interval="1h", limit=2)
    return data[-1]["close"] if data else None


async def compute_portfolio(user: User, store: AppStore) -> dict:
    signals = store.signals.list_for_tenant(user.tenant_id, limit=200)
    positions: list[dict] = []
    total_pnl = 0.0
    total_value = 0.0
    price_cache: dict[str, float | None] = {}

    for s in signals:
        p = s.payload
        if p.get("direction") not in ("BUY", "SELL"):
            continue
        symbol = p.get("asset", "")
        if symbol not in price_cache:
            price_cache[symbol] = await _last_price(symbol)
        price = price_cache[symbol]
        entry = float(p.get("entry") or 0)
        size = float(p.get("position_size") or 0)
        direction = 1 if p.get("direction") == "BUY" else -1
        pnl = (price - entry) * size * direction if price else 0.0
        value = (price or entry) * size
        total_pnl += pnl
        total_value += value
        positions.append(
            {
                "id": s.id,
                "asset": symbol,
                "direction": p.get("direction"),
                "entry": entry,
                "current_price": price,
                "size": round(size, 8),
                "value": round(value, 2),
                "pnl": round(pnl, 2),
            }
        )

    return {
        "total_pnl": round(total_pnl, 2),
        "total_value": round(total_value, 2),
        "pnl_pct": round((total_pnl / user.capital * 100), 2) if user.capital else 0.0,
        "positions": positions,
    }

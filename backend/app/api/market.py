"""Routes de données marché : OHLCV pour le graphique (authentifié)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query

from app.core.deps import current_user, store_dep
from app.data import symbols as symbols_catalog
from app.data.heatmap import get_heatmap
from app.data.ohlcv import get_ohlcv
from app.models.entities import User
from app.models.signal import Timeframe
from app.repositories.store import AppStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/market", tags=["market"])

_TF_INTERVAL = {
    Timeframe.SCALP: "5m",
    Timeframe.INTRADAY: "15m",
    Timeframe.SWING: "1h",
    Timeframe.POSITION: "4h",
}


@router.get("/ohlcv")
async def ohlcv(
    asset: str = Query("BTC/USDT"),
    timeframe: Timeframe = Query(Timeframe.SWING),
    limit: int = Query(200, ge=20, le=500),
    _user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    interval = _TF_INTERVAL.get(timeframe, "1h")
    data = await get_ohlcv(asset, interval=interval, limit=limit)
    # Ingestion best-effort vers TimescaleDB (no-op en mode in-memory).
    try:
        store.market.upsert_ohlcv(asset, interval, data)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ingestion OHLCV échouée (%s)", exc)
    return data


@router.get("/heatmap")
async def heatmap(
    user: User = Depends(current_user),
) -> list[dict]:
    """Variation 24h des actifs de la watchlist (heatmap marché)."""
    symbols = user.watchlist or ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    return await get_heatmap(symbols)


@router.get("/symbols")
async def list_symbols(
    q: str | None = Query(default=None, description="Filtre texte (ex. BTC, EUR, AAPL)"),
    asset_class: str | None = Query(default=None, description="crypto | forex | stock"),
    _user: User = Depends(current_user),
) -> dict:
    """Catalogue multi-marchés (crypto / forex / actions) + recherche."""
    return {
        "results": symbols_catalog.search(q, asset_class, limit=100),
        "classes": list(symbols_catalog.catalog().keys()),
    }

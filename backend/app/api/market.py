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
    mix: bool = Query(default=False, description="Mélange multi-marchés (crypto+forex+actions)"),
    user: User = Depends(current_user),
) -> list[dict]:
    """Variation 24h : watchlist par défaut, ou un panel multi-marchés si mix=true."""
    if mix:
        cat = symbols_catalog.catalog()
        symbols = cat["crypto"][:6] + cat["forex"][:5] + cat["stock"][:6]
    else:
        symbols = user.watchlist or ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    return await get_heatmap(symbols)


@router.get("/sessions")
async def sessions(_user: User = Depends(current_user)) -> dict:
    """Sessions de trading mondiales (Asie/Londres/New York) + celle(s) actuellement ouverte(s)."""
    from app.data import sessions as sessions_mod

    return sessions_mod.overview()


@router.get("/symbols")
async def list_symbols(
    q: str | None = Query(default=None, description="Filtre texte (ex. BTC, EUR, AAPL)"),
    asset_class: str | None = Query(default=None, description="crypto | forex | stock"),
    session: str | None = Query(default=None, description="asian | london | newyork"),
    _user: User = Depends(current_user),
) -> dict:
    """Catalogue multi-marchés (crypto / forex / actions) + recherche, filtrable par session."""
    if session:
        from app.data import sessions as sessions_mod
        results = sessions_mod.session_universe(session)
        if asset_class:
            results = [r for r in results if r["asset_class"] == asset_class]
        if q:
            results = [r for r in results if q.strip().upper() in r["symbol"].upper()]
    else:
        results = symbols_catalog.search(q, asset_class, limit=100)
    return {"results": results, "classes": list(symbols_catalog.catalog().keys())}

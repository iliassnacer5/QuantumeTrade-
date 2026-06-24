"""Routes de données marché : OHLCV pour le graphique (authentifié)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.deps import current_user
from app.data.ohlcv import get_ohlcv
from app.models.entities import User
from app.models.signal import Timeframe

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
) -> list[dict]:
    interval = _TF_INTERVAL.get(timeframe, "1h")
    return await get_ohlcv(asset, interval=interval, limit=limit)

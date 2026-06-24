"""Routes de Backtesting (M6) — authentifié, isolé par tenant, données réelles horodatées."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.backtest.engine import run_backtest
from app.backtest.schemas import BacktestConfig, BacktestReport
from app.core.deps import current_user, store_dep
from app.data.ohlcv import get_ohlcv
from app.data.synthetic import generate_candles
from app.domain.indicators import Candle
from app.models.entities import User
from app.repositories.store import AppStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/backtest", tags=["backtest"])

_STEP = {"5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}


async def _load_history(symbol: str, timeframe: str, limit: int = 500) -> list[Candle]:
    """Charge l'historique OHLCV horodaté ; repli synthétique si indisponible."""
    try:
        rows = await get_ohlcv(symbol, interval=timeframe, limit=limit)
        if len(rows) >= 100:
            return [
                Candle(
                    open=r["open"], high=r["high"], low=r["low"], close=r["close"],
                    volume=r.get("volume", 0.0),
                    timestamp=datetime.fromtimestamp(r["time"], UTC),
                )
                for r in rows
            ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Historique %s indisponible (%s), repli synthétique", symbol, exc)

    step = _STEP.get(timeframe, 3600)
    base = datetime.now(UTC) - timedelta(seconds=step * limit)
    return [
        Candle(c.open, c.high, c.low, c.close, c.volume, timestamp=base + timedelta(seconds=step * i))
        for i, c in enumerate(generate_candles(n=limit, seed=abs(hash(symbol)) % 10_000))
    ]


@router.post("/run", response_model=BacktestReport)
async def run(
    config: BacktestConfig,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> BacktestReport:
    candles = await _load_history(config.symbol, config.timeframe)
    if len(candles) < 100:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Historique insuffisant pour le backtest")
    try:
        report = await run_backtest(config, candles, tenant_id=user.tenant_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Erreur backtest")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)) from exc
    store.backtests.save_report(report)
    return report


@router.get("/reports", response_model=list[BacktestReport])
async def reports(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> list[BacktestReport]:
    return store.backtests.list_for_tenant(user.tenant_id, limit=20)

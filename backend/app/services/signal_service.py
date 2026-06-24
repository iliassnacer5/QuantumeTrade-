"""Service de génération de signaux — la boucle de valeur du MVP.

Données (Binance ou synthétique) -> Agents (Technique + Sentiment) -> Master -> Signal Engine
-> persistance -> diffusion WebSocket -> alerte.
"""

from __future__ import annotations

import logging

from app.data import binance, news as news_mod
from app.data.synthetic import generate_candles
from app.domain.indicators import Candle
from app.domain.risk import RiskParams
from app.models.entities import User
from app.models.signal import SignalCard, Timeframe
from app.realtime import bus
from app.repositories.store import AppStore
from app.signal_engine.engine import generate_signal
from app.alerts.notifier import notify_signal

logger = logging.getLogger(__name__)

# Profil de risque -> % du capital risqué par trade
_RISK_PCT = {"conservative": 0.5, "moderate": 1.0, "aggressive": 2.0}

# Timeframe -> intervalle Binance
_TF_INTERVAL = {
    Timeframe.SCALP: "5m",
    Timeframe.INTRADAY: "15m",
    Timeframe.SWING: "1h",
    Timeframe.POSITION: "4h",
}


async def _load_candles(symbol: str, timeframe: Timeframe) -> list[Candle]:
    """Charge les bougies via Binance, avec repli synthétique si indisponible (offline/test)."""
    interval = _TF_INTERVAL.get(timeframe, "1h")
    try:
        candles = await binance.fetch_klines(symbol, interval=interval, limit=200)
        if len(candles) >= 60:
            return candles
        logger.warning("Backfill insuffisant pour %s, repli synthétique", symbol)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Binance indisponible (%s), repli synthétique", exc)
    return generate_candles()


async def generate_for_user(
    user: User,
    store: AppStore,
    *,
    asset: str,
    timeframe: Timeframe = Timeframe.SWING,
    notify: bool = True,
) -> SignalCard:
    """Génère, persiste, diffuse et notifie un signal pour un utilisateur."""
    candles = await _load_candles(asset, timeframe)
    news_items = await news_mod.fetch_news(asset)

    risk = RiskParams(
        capital=user.capital,
        risk_per_trade_pct=_RISK_PCT.get(user.risk_profile, 1.0),
    )

    card = await generate_signal(
        asset=asset,
        candles=candles,
        news=news_items,
        risk=risk,
        timeframe=timeframe,
    )

    # Persistance (isolée par tenant)
    payload = card.model_dump(mode="json")
    stored = store.signals.add(user.tenant_id, payload)
    payload["id"] = stored.id

    # Diffusion temps réel (Redis pub/sub si actif, sinon hub mémoire) + alerte
    await bus.publish(user.tenant_id, {"type": "signal", "data": payload})
    if notify:
        await notify_signal(
            card,
            email=user.email if getattr(user, "alert_email", True) else None,
            telegram_chat_id=getattr(user, "telegram_chat_id", None),
        )

    return card

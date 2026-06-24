"""Service de génération de signaux — la boucle de valeur du MVP.

Données (Binance ou synthétique) -> Agents (Technique + Sentiment) -> Master -> Signal Engine
-> persistance -> diffusion WebSocket -> alerte.
"""

from __future__ import annotations

import logging

from app.data import macro as macro_data_mod, markets, news as news_mod
from app.domain.indicators import Candle
from app.domain.risk import RiskParams
from app.models.entities import User
from app.models.signal import Timeframe
from app.models.signal import SignalCard
from app.realtime import bus
from app.repositories.store import AppStore
from app.services import journal_service, risk_service
from app.signal_engine.engine import generate_signal
from app.alerts.notifier import notify_signal

logger = logging.getLogger(__name__)

# Profil de risque -> % du capital risqué par trade
_RISK_PCT = {"conservative": 0.5, "moderate": 1.0, "aggressive": 2.0}

_TF_INTERVAL = {
    Timeframe.SCALP: "5m",
    Timeframe.INTRADAY: "15m",
    Timeframe.SWING: "1h",
    Timeframe.POSITION: "4h",
}


async def _load_candles(symbol: str, timeframe: Timeframe) -> list[Candle]:
    """Charge les bougies selon la classe d'actif (crypto/actions/forex), repli synthétique inclus."""
    return await markets.load_candles(symbol, interval=_TF_INTERVAL.get(timeframe, "1h"), limit=200)


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
    macro_ctx = await macro_data_mod.fetch_macro_data()

    risk = RiskParams(
        capital=user.capital,
        risk_per_trade_pct=_RISK_PCT.get(user.risk_profile, 1.0),
    )

    # Contexte de risque courant (exposition) + apprentissage Journal (poids dynamiques).
    rs = risk_service.compute_status(user, store)
    risk_context = {"exposure_pct": rs.exposure_pct, "drawdown_pct": 0.0}
    journal_mult = journal_service.compute_multipliers(store, user.tenant_id)

    card = await generate_signal(
        asset=asset,
        candles=candles,
        news=news_items,
        risk=risk,
        timeframe=timeframe,
        macro_data=macro_ctx,
        risk_context=risk_context,
        journal_multipliers=journal_mult,
    )

    # Persistance (isolée par tenant)
    payload = card.model_dump(mode="json")
    stored = store.signals.add(user.tenant_id, payload)
    payload["id"] = stored.id

    # Boucle d'apprentissage : enregistre l'issue (open) + scores d'agents pour le Journal.
    journal_service.record_signal(store, user.tenant_id, card, stored.id)

    # Copy-trading (Phase 4) : si l'utilisateur est un trader public, réplique vers ses suiveurs.
    try:
        from app.services import copytrading_service
        await copytrading_service.on_leader_signal(store, user.tenant_id, card)
    except Exception as exc:  # noqa: BLE001 — la copie ne doit jamais casser la génération
        logger.warning("Copy-trading fan-out échoué (%s)", exc)

    # Diffusion temps réel (Redis pub/sub si actif, sinon hub mémoire) + alerte
    await bus.publish(user.tenant_id, {"type": "signal", "data": payload})
    if notify:
        await notify_signal(
            card,
            email=user.email if user.alert_email else None,
            telegram_chat_id=user.telegram_chat_id if user.alert_telegram else None,
            webhook_url=user.webhook_url if user.alert_webhook else None,
            sms_to=user.phone if user.alert_sms else None,
            push_token=user.push_token,
        )

    return card

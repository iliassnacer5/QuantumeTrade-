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


async def scan_market(
    asset_class: str | None = None,
    timeframe: str = "1h",
    limit: int = 20,
    high_conviction_only: bool = False,
) -> list[dict]:
    """Scanne un marché et classe les symboles par conviction (rapide : analyse technique).

    Retourne TOUS les symboles analysés, triés par score de conviction, avec un flag
    `high_conviction` (ADX>25 + tendance franche). Le multi-timeframe complet et les news sont
    calculés à la demande quand l'utilisateur ouvre un symbole (« Analyser »).
    """
    from app.data import symbols as symbols_catalog
    from app.domain import ta
    from app.models.signal import Direction

    universe = symbols_catalog.search(asset_class=asset_class, limit=limit)
    results: list[dict] = []
    for item in universe:
        sym = item["symbol"]
        try:
            candles = await markets.load_candles(sym, interval=timeframe, limit=200)
            if len(candles) < 60:
                continue
            a = ta.analyze(candles)
            m = a["metrics"]
            adx = m.get("adx", 0) or 0
            direction = Direction.BUY if a["score"] > 0.12 else Direction.SELL if a["score"] < -0.12 else Direction.HOLD
            high_conv = direction != Direction.HOLD and adx > 25 and abs(a["score"]) > 0.3
            conviction = round(abs(a["score"]) * (1 + adx / 50), 3)
            results.append({
                "symbol": sym,
                "asset_class": item["asset_class"],
                "direction": direction.value,
                "score": a["score"],
                "adx": round(adx, 1),
                "adx_state": m.get("adx_state"),
                "trend": m.get("trend"),
                "rsi": m.get("rsi"),
                "price": m.get("price"),
                "conviction": conviction,
                "high_conviction": high_conv,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scan %s échoué (%s)", sym, exc)
    if high_conviction_only:
        results = [r for r in results if r["high_conviction"]]
    results.sort(key=lambda r: (r["high_conviction"], r["conviction"]), reverse=True)
    return results


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

    # Confirmation multi-timeframe (1h/4h/1j) + marqueur haute-conviction.
    from app.signal_engine import mtf
    card.mtf = await mtf.confirm(asset, card.direction)
    adx = card.metrics.get("adx")
    card.high_conviction = bool(
        card.direction.value != "HOLD"
        and adx and adx > 25
        and card.consensus_pct >= 70
        and card.mtf.get("aligned", 0) >= 2
    )

    # Persistance (isolée par tenant)
    payload = card.model_dump(mode="json")
    stored = store.signals.add(user.tenant_id, payload)
    payload["id"] = stored.id

    # Observabilité (Phase 5)
    from app.core import metrics
    metrics.inc("signals_generated_total", direction=card.direction.value if hasattr(card.direction, "value") else str(card.direction))

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

"""Alertes sur la stratégie active — transforme l'outil en assistant quotidien.

Pour chaque utilisateur ayant choisi une stratégie, surveille ses paires (watchlist) sur le marché
en direct. Dès que la stratégie passe à un NOUVEAU signal directionnel (BUY/SELL), envoie une alerte
(email / Telegram / push selon ses préférences). Anti-spam : on ne notifie qu'au CHANGEMENT d'état.
"""

from __future__ import annotations

import logging

from app.alerts import notifier
from app.data import markets
from app.domain import indicators as ind
from app.domain.risk import RiskParams, compute_levels
from app.models.signal import Direction
from app.strategies import get_strategy

logger = logging.getLogger(__name__)

_STATE = "strategy_alert_state"
_DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]


async def check_strategy_alerts(store) -> int:
    """Parcourt les utilisateurs avec stratégie active et notifie les nouveaux signaux. -> nb d'alertes."""
    sent = 0
    try:
        users = store.users.list_all()
    except Exception:  # noqa: BLE001
        return 0

    for user in users:
        sel = store.records.get("strategy_choice", user.tenant_id)
        strat = get_strategy((sel or {}).get("strategy", "")) if sel else None
        if strat is None:
            continue
        symbols = (getattr(user, "watchlist", None) or _DEFAULT_SYMBOLS)[:5]
        for symbol in symbols:
            try:
                if await _check_symbol(store, user, strat, symbol):
                    sent += 1
            except Exception as exc:  # noqa: BLE001 — un symbole ne bloque pas les autres
                logger.warning("Alerte stratégie %s/%s échouée (%s)", user.tenant_id, symbol, exc)
    return sent


async def _check_symbol(store, user, strat, symbol: str) -> bool:
    from app.core.config import get_settings

    # Timeframe configurable — défaut 4h : le seul combo à alpha positif mesuré (cf. PLAN_MAITRE).
    tf = get_settings().strategy_alerts_timeframe
    candles = await markets.load_candles(symbol, interval=tf, limit=200)
    # On n'alerte que sur des données réelles (jamais sur du synthétique).
    if not markets.is_real(symbol):
        return False
    direction = strat.fn(candles)
    key = f"{user.tenant_id}:{symbol}:{strat.id}"
    prev = (store.records.get(_STATE, key) or {}).get("direction")
    new_dir = direction.value

    # Mémorise l'état courant (pour détecter les changements).
    store.records.put(_STATE, key, {"direction": new_dir, "strategy": strat.id}, tenant_id=user.tenant_id)

    # Alerte uniquement sur un NOUVEAU signal directionnel.
    if new_dir == Direction.HOLD.value or new_dir == prev:
        return False

    entry = candles[-1].close
    atr_v = ind.atr(candles, 14) or (entry * 0.01)
    levels = compute_levels(direction, entry, atr_v, RiskParams(capital=user.capital, risk_per_trade_pct=1.0))
    msg = (
        f"📊 {strat.name} — {symbol} : signal {new_dir}\n"
        f"Entrée ~{round(entry, 4)} | SL {levels.stop_loss} | TP {levels.take_profit_1} "
        f"(R/R 1:{levels.risk_reward}). Aide à la décision, pas un conseil."
    )
    await _notify(user, f"Signal {new_dir} — {symbol}", msg)
    logger.info("Alerte stratégie envoyée : %s %s %s", user.tenant_id, symbol, new_dir)

    # FORWARD TEST AUTO (opt-in) : ouvre le trade PAPIER automatiquement (risque 1%, SL/TP inclus).
    # C'est le juge final de l'edge : des semaines de trades réels simulés, sans intervention.
    if (store.records.get("auto_trade", user.tenant_id) or {}).get("enabled"):
        from app.core.config import get_settings
        from app.services import edge_map_service

        s = get_settings()
        # Règle d'or (plan maître) : on n'auto-trade QUE les combos verts de la carte de l'edge
        # (alpha>0 + PF>=1,2 out-of-sample). Ailleurs : alerte seulement, pas de trade.
        if s.auto_trade_green_only and not edge_map_service.is_combo_green(
            store, strat.id, symbol, min_streak=s.edge_min_green_streak
        ):
            logger.info("Auto-trade ignoré (%s/%s pas vert sur la carte de l'edge)", strat.id, symbol)
        else:
            await _auto_paper_trade(store, user, symbol, new_dir, levels)
    return True


async def _auto_paper_trade(store, user, symbol: str, direction: str, levels) -> None:
    """Ouvre automatiquement le trade papier correspondant au signal (best-effort, garde-fous actifs)."""
    from app.services import execution_service

    try:
        conns = [c for c in execution_service.list_connections(store, user.tenant_id) if c["mode"] == "paper"]
        conn = conns[0] if conns else execution_service.connect_broker(
            store, user.tenant_id, broker="paper", api_key="", api_secret="", mode="paper")
        qty = levels.position_size or 0.0  # déjà dimensionnée à 1% de risque par compute_levels
        if qty <= 0:
            return
        await execution_service.place_order(
            store, user.tenant_id, conn_id=conn["id"], symbol=symbol,
            side="buy" if direction == "BUY" else "sell", qty=round(qty, 6),
            stop_loss=levels.stop_loss, take_profit=levels.take_profit_1,
        )
        logger.info("Auto-trade papier ouvert : %s %s qty=%.6f", symbol, direction, qty)
    except Exception as exc:  # noqa: BLE001 — garde-fous (exposition, synthétique) peuvent refuser : normal
        logger.info("Auto-trade papier refusé/échoué (%s) : %s", symbol, exc)


async def _notify(user, subject: str, msg: str) -> None:
    if getattr(user, "alert_email", False) and user.email:
        await notifier.send_email(user.email, subject, msg)
    if getattr(user, "alert_telegram", False) and getattr(user, "telegram_chat_id", None):
        await notifier.send_telegram(user.telegram_chat_id, msg)
    if getattr(user, "push_token", None):
        await notifier.send_push(user.push_token, msg)

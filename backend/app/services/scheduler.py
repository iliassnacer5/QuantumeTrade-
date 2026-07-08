"""Automatisation quotidienne — pré-calcul des trades fiables + envoi du digest.

Boucle asyncio (sans dépendance native) lancée au démarrage : chaque jour à l'heure configurée
(`daily_digest_hour` UTC), elle calcule la sélection (`daily_picks`), la met en cache, et notifie
les utilisateurs ayant activé le digest, via leurs canaux d'alerte (email / Telegram / push).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.alerts import notifier
from app.core.config import get_settings
from app.services import signal_service

logger = logging.getLogger(__name__)


def _format_digest(picks: list[dict]) -> str:
    if not picks:
        return "Aucun trade fiable à forte conviction aujourd'hui. Mieux vaut s'abstenir."
    lines = ["📈 Trades du jour :"]
    for p in picks:
        bt = p.get("backtest") or {}
        tag = "✅ confirmé" if p.get("tier") == "confirmed" else "👀 à surveiller (non confirmé)"
        bt_txt = f" — backtest {bt.get('win_rate')}% / PF {bt.get('profit_factor')}" if bt else ""
        lines.append(f"• {p['symbol']} {p['direction']} [{tag}] — ADX {p['adx']}{bt_txt}")
    lines.append("\nAide à la décision, pas un conseil. Vérifie R/R et taille de position avant d'agir.")
    return "\n".join(lines)


async def run_daily_digest(store) -> dict:  # noqa: ANN001
    """Calcule la sélection du jour, la met en cache et envoie le digest aux abonnés."""
    today = datetime.now(UTC).date().isoformat()
    picks = await signal_service.daily_picks()
    rec = store.records.put(
        "daily_picks", today, {"date": today, "picks": picks, "generated_at": datetime.now(UTC).isoformat()},
    )
    text = _format_digest(picks)
    sent = 0
    try:
        users = store.users.list_all()
    except Exception:  # noqa: BLE001
        users = []
    for user in users:
        if not getattr(user, "daily_digest", False):
            continue
        try:
            if user.alert_email and user.email:
                await notifier.send_email(user.email, "Quantum Trade AI — Trades du jour", text)
            if user.alert_telegram and user.telegram_chat_id:
                await notifier.send_telegram(user.telegram_chat_id, text)
            if user.push_token:
                await notifier.send_push(user.push_token, "Trades du jour disponibles 📈")
            sent += 1
        except Exception as exc:  # noqa: BLE001 — un échec ne doit pas bloquer les autres
            logger.warning("Digest non envoyé à %s (%s)", user.email, exc)
    logger.info("Digest quotidien : %d trades, %d utilisateurs notifiés", len(picks), sent)
    return rec


async def daily_loop() -> None:
    """Boucle : attend l'heure du jour configurée puis lance le digest, en continu."""
    from app.repositories.store import get_store

    while True:
        settings = get_settings()
        now = datetime.now(UTC)
        target = now.replace(hour=settings.daily_digest_hour, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        await asyncio.sleep(max(60, (target - now).total_seconds()))
        try:
            await run_daily_digest(get_store())
        except Exception as exc:  # noqa: BLE001
            logger.exception("Échec du digest quotidien (%s)", exc)


async def learning_loop() -> None:
    """Apprentissage continu : résout les signaux ouverts (win/loss) pour TOUS les tenants.

    Plus il y a de trades résolus, plus les multiplicateurs de fiabilité par agent s'affinent et
    plus les signaux émis deviennent fiables (le Master pondère selon ce qui a marché)."""
    from app.repositories.store import get_store
    from app.services import journal_service

    while True:
        await asyncio.sleep(max(60, get_settings().learning_interval))
        store = get_store()
        try:
            tenants = {u.tenant_id for u in store.users.list_all()}
        except Exception:  # noqa: BLE001
            tenants = set()
        total = 0
        for tid in tenants:
            try:
                total += await journal_service.auto_resolve(store, tid)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Apprentissage tenant %s échoué (%s)", tid, exc)
        if total:
            logger.info("Apprentissage : %d signal(aux) résolu(s) -> pondérations affinées", total)


async def strategy_alerts_loop() -> None:
    """Surveille les stratégies actives et envoie une alerte à chaque nouveau signal directionnel."""
    from app.repositories.store import get_store
    from app.services import strategy_alert_service

    while True:
        await asyncio.sleep(max(120, get_settings().strategy_alerts_interval))
        try:
            sent = await strategy_alert_service.check_strategy_alerts(get_store())
            if sent:
                logger.info("Alertes stratégie : %d notification(s) envoyée(s)", sent)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Échec des alertes stratégie (%s)", exc)


async def edge_sweep_loop() -> None:
    """Sweep NOCTURNE de la carte de l'edge : walk-forward de toutes les stratégies × symboles × TF.

    Phase B du plan maître : savoir en continu OÙ il y a un edge exploitable (et où il n'y en a
    pas). Premier passage ~10 min après le boot, puis toutes les `edge_sweep_interval_hours` h."""
    from app.repositories.store import get_store
    from app.services import edge_map_service

    await asyncio.sleep(600)  # laisser le démarrage se stabiliser
    while True:
        s = get_settings()
        if s.edge_sweep_enabled:
            try:
                payload = await edge_map_service.run_edge_sweep(get_store())
                logger.info("Carte de l'edge mise à jour : %s", payload.get("note"))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Échec du sweep de la carte de l'edge (%s)", exc)
        await asyncio.sleep(max(3600, s.edge_sweep_interval_hours * 3600))


async def positions_loop() -> None:
    """Surveillance continue des positions papier : clôture auto dès qu'un SL/TP est atteint."""
    from app.repositories.store import get_store
    from app.services import execution_service

    while True:
        interval = max(15, get_settings().position_monitor_interval)
        await asyncio.sleep(interval)
        try:
            closed = await execution_service.monitor_positions(get_store())
            if closed:
                logger.info("Moniteur positions : %d position(s) clôturée(s) automatiquement", closed)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Échec du moniteur de positions (%s)", exc)

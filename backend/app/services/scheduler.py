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
    lines = ["📈 Trades du jour (haute-conviction + backtest fiable) :"]
    for p in picks:
        bt = p.get("backtest", {})
        lines.append(
            f"• {p['symbol']} {p['direction']} — ADX {p['adx']}, "
            f"backtest {bt.get('win_rate')}% réussite / PF {bt.get('profit_factor')}"
        )
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

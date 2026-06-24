"""Notificateurs multicanal (MVP : email via Resend, Telegram).

Si les clés ne sont pas configurées, les envois sont journalisés (no-op gracieux) afin que le
pipeline complet fonctionne en dev/test sans dépendances externes.
"""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.models.signal import SignalCard

logger = logging.getLogger(__name__)


def format_signal(card: SignalCard) -> str:
    tps = " / ".join(
        str(t) for t in [card.take_profit_1, card.take_profit_2, card.take_profit_3] if t is not None
    )
    return (
        f"[{card.direction.value}] {card.asset}\n"
        f"Entrée: {card.entry} | SL: {card.stop_loss} | TP: {tps}\n"
        f"R/R: {card.risk_reward} | Confiance: {card.confidence}% | {card.timeframe.value}\n"
        f"{card.rationale}"
    )


async def send_telegram(chat_id: str, text: str) -> bool:
    s = get_settings()
    if not s.telegram_bot_token:
        logger.info("[telegram:noop] %s", text.replace("\n", " | "))
        return False
    try:
        import httpx

        url = f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={"chat_id": chat_id, "text": text})
            resp.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Envoi Telegram échoué (%s)", exc)
        return False


async def send_email(to: str, subject: str, text: str) -> bool:
    s = get_settings()
    if not s.resend_api_key:
        logger.info("[email:noop] to=%s subject=%s", to, subject)
        return False
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {s.resend_api_key}"},
                json={"from": s.email_from, "to": [to], "subject": subject, "text": text},
            )
            resp.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Envoi email échoué (%s)", exc)
        return False


async def notify_signal(card: SignalCard, *, email: str | None = None, telegram_chat_id: str | None = None) -> None:
    text = format_signal(card)
    if email:
        await send_email(email, f"Nouveau signal {card.asset} — {card.direction.value}", text)
    if telegram_chat_id:
        await send_telegram(telegram_chat_id, text)

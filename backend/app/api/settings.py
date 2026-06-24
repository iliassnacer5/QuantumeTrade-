"""Route Paramètres : watchlist, limites de risque, préférences d'alerte."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.models.schemas import SettingsRequest, SettingsResponse
from app.repositories.store import AppStore

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _to_response(u: User) -> SettingsResponse:
    return SettingsResponse(
        watchlist=u.watchlist,
        max_exposure_pct=u.max_exposure_pct,
        max_daily_signals=u.max_daily_signals,
        daily_loss_limit_pct=u.daily_loss_limit_pct,
        alert_email=u.alert_email,
        alert_telegram=u.alert_telegram,
        telegram_chat_id=u.telegram_chat_id,
        alert_webhook=u.alert_webhook,
        webhook_url=u.webhook_url,
        alert_sms=u.alert_sms,
        phone=u.phone,
        mfa_enabled=u.mfa_enabled,
    )


@router.get("", response_model=SettingsResponse)
async def get_settings_route(user: User = Depends(current_user)) -> SettingsResponse:
    return _to_response(user)


@router.patch("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsRequest,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> SettingsResponse:
    if body.watchlist is not None:
        user.watchlist = [s.strip().upper() for s in body.watchlist if s.strip()]
    if body.max_exposure_pct is not None:
        user.max_exposure_pct = body.max_exposure_pct
    if body.max_daily_signals is not None:
        user.max_daily_signals = body.max_daily_signals
    if body.daily_loss_limit_pct is not None:
        user.daily_loss_limit_pct = body.daily_loss_limit_pct
    if body.alert_email is not None:
        user.alert_email = body.alert_email
    if body.alert_telegram is not None:
        user.alert_telegram = body.alert_telegram
    if body.telegram_chat_id is not None:
        user.telegram_chat_id = body.telegram_chat_id or None
    if body.alert_webhook is not None:
        user.alert_webhook = body.alert_webhook
    if body.webhook_url is not None:
        user.webhook_url = body.webhook_url or None
    if body.alert_sms is not None:
        user.alert_sms = body.alert_sms
    if body.phone is not None:
        user.phone = body.phone or None
    store.users.update(user)
    return _to_response(user)

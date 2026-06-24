"""Route d'onboarding : profil de risque, capital, marchés suivis."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import _to_response
from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.models.schemas import OnboardingRequest, UserResponse
from app.repositories.store import AppStore

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.post("", response_model=UserResponse)
async def onboard(
    body: OnboardingRequest,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> UserResponse:
    user.risk_profile = body.risk_profile
    user.capital = body.capital
    user.watchlist = body.watchlist
    user.onboarded = True
    store.users.update(user)
    return _to_response(user, store)

"""Route d'état du risque (exposition, signaux du jour, dépassements)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import risk_service

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/status")
async def status(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    return risk_service.compute_status(user, store).as_dict()

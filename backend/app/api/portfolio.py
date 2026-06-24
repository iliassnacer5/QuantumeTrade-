"""Route portefeuille : P&L latent et positions dérivées des signaux."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("")
async def portfolio(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    return await portfolio_service.compute_portfolio(user, store)

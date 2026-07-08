"""Portefeuille virtuel (paper) — solde simulé + statistiques de fiabilité."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import wallet_service

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.get("")
async def wallet(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    """État du portefeuille virtuel : solde, équité, P&L et statistiques sur les trades papier."""
    return await wallet_service.compute_wallet(store, user.tenant_id)


@router.post("/reset")
async def reset_wallet(
    starting_balance: float = 10_000.0,
    clear_orders: bool = True,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Repart à zéro : nouveau solde de départ (et efface l'historique papier par défaut)."""
    wallet_service.reset(store, user.tenant_id, starting_balance, clear_orders)
    return await wallet_service.compute_wallet(store, user.tenant_id)

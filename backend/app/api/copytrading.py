"""Copy-trading (Phase 4) — réservé Elite (copy_trading).

Publier son profil (opt-in), consulter le classement, suivre un top trader avec contrôles de risque,
et suivre ses commissions (partage de revenus).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import store_dep
from app.core.plans import require_feature
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import copytrading_service as copy

router = APIRouter(prefix="/api/copytrading", tags=["copytrading"])


class PublishRequest(BaseModel):
    display_name: str = "Trader"


class FollowRequest(BaseModel):
    leader_tenant: str
    allocation_pct: float = 5.0
    max_per_trade: float = 1000.0
    min_confidence: int = 60


@router.get("/leaderboard")
async def leaderboard(
    user: User = Depends(require_feature("copy_trading")),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return copy.leaderboard(store)


@router.post("/publish")
async def publish(
    body: PublishRequest,
    user: User = Depends(require_feature("copy_trading")),
    store: AppStore = Depends(store_dep),
) -> dict:
    return copy.publish_profile(store, user.tenant_id, body.display_name)


@router.delete("/publish")
async def unpublish(
    user: User = Depends(require_feature("copy_trading")),
    store: AppStore = Depends(store_dep),
) -> dict:
    return {"unpublished": copy.unpublish_profile(store, user.tenant_id)}


@router.get("/following")
async def following(
    user: User = Depends(require_feature("copy_trading")),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return copy.following(store, user.tenant_id)


@router.post("/follow", status_code=status.HTTP_201_CREATED)
async def follow(
    body: FollowRequest,
    user: User = Depends(require_feature("copy_trading")),
    store: AppStore = Depends(store_dep),
) -> dict:
    try:
        return copy.follow(
            store, user.tenant_id, body.leader_tenant,
            allocation_pct=body.allocation_pct, max_per_trade=body.max_per_trade, min_confidence=body.min_confidence,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc


@router.delete("/follow/{follow_id}")
async def unfollow(
    follow_id: str,
    user: User = Depends(require_feature("copy_trading")),
    store: AppStore = Depends(store_dep),
) -> dict:
    if not copy.unfollow(store, user.tenant_id, follow_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Suivi introuvable")
    return {"unfollowed": True}


@router.get("/commissions")
async def commissions(
    user: User = Depends(require_feature("copy_trading")),
    store: AppStore = Depends(store_dep),
) -> dict:
    return copy.commissions(store, user.tenant_id)

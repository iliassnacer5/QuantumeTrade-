"""Endpoint des droits (entitlements) du plan courant — Phase 3.

Le frontend l'utilise pour afficher/masquer les fonctionnalités payantes (Copilot, backtest, journal…).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import current_user, store_dep
from app.core.plans import FEATURE_MIN_PLAN, features_for, plan_of
from app.models.entities import User
from app.repositories.store import AppStore

router = APIRouter(prefix="/api/plan", tags=["plan"])


@router.get("")
async def my_plan(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    plan = plan_of(user, store)
    return {
        "plan": plan,
        "features": features_for(plan),
        "feature_requirements": FEATURE_MIN_PLAN,
    }

"""Droits par plan (entitlements) et garde-fou de gating — Phase 3.

Source de vérité unique des fonctionnalités débloquées par chaque plan. Utilisé :
- par les endpoints (dépendance `require_feature`) pour bloquer l'accès aux features payantes ;
- par le frontend (endpoint `/api/plan`) pour afficher/masquer l'UI.

Le plan vit sur le `Tenant` (facturation par compte). Hiérarchie : free < starter < pro < elite.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.repositories.store import AppStore

# Ordre hiérarchique (un plan hérite des features des plans inférieurs).
PLAN_ORDER = ["free", "starter", "pro", "elite", "enterprise"]

# Features et plan minimum requis.
FEATURE_MIN_PLAN: dict[str, str] = {
    "signals": "free",
    "multichannel_alerts": "starter",
    "multi_market": "starter",
    "backtesting": "pro",
    "copilot": "pro",
    "journal": "pro",
    "team": "pro",
    "api_access": "elite",
    "copy_trading": "elite",
    "auto_execution": "elite",
}


def _rank(plan: str) -> int:
    return PLAN_ORDER.index(plan) if plan in PLAN_ORDER else 0


def plan_allows(plan: str, feature: str) -> bool:
    """Vrai si `plan` débloque `feature`."""
    required = FEATURE_MIN_PLAN.get(feature, "elite")
    return _rank(plan) >= _rank(required)


def features_for(plan: str) -> dict[str, bool]:
    """Carte feature -> accessible, pour ce plan."""
    return {f: plan_allows(plan, f) for f in FEATURE_MIN_PLAN}


def plan_of(user: User, store: AppStore) -> str:
    """Plan effectif de l'utilisateur (porté par son tenant)."""
    tenant = store.tenants.get(user.tenant_id)
    return tenant.plan if tenant else "free"


def require_feature(feature: str):
    """Fabrique une dépendance FastAPI qui exige `feature` (sinon 402 Payment Required)."""

    async def _guard(
        user: User = Depends(current_user),
        store: AppStore = Depends(store_dep),
    ) -> User:
        plan = plan_of(user, store)
        if not plan_allows(plan, feature):
            required = FEATURE_MIN_PLAN.get(feature, "elite")
            raise HTTPException(
                status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Fonctionnalité '{feature}' réservée au plan '{required}' ou supérieur "
                f"(plan actuel : '{plan}'). Mettez à niveau pour y accéder.",
            )
        return user

    return _guard

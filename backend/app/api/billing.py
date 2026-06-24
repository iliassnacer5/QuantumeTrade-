"""M10 — Facturation (Stripe). Stub MVP : Free + Starter.

En prod : créer une session Checkout Stripe et mettre à jour le plan via webhook signé.
Ici, on expose les plans et un endpoint de changement de plan (simulé) pour dérouler le flux.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.auth import _to_response
from app.core.config import get_settings
from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.models.schemas import UserResponse
from app.repositories.store import AppStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])

PLANS = [
    {"id": "free", "price": 0, "markets": 1, "features": ["signaux limités", "alertes basiques"]},
    {"id": "starter", "price": 29, "markets": 3, "features": ["signaux illimités", "alertes multicanal"]},
    {"id": "pro", "price": 79, "markets": 999, "features": ["tous marchés", "backtesting", "AI Copilot"]},
    {"id": "elite", "price": 199, "markets": 999, "features": ["API", "copy-trading", "exécution auto"]},
]


@router.get("/plans")
async def plans() -> list[dict]:
    return PLANS


@router.post("/checkout/{plan_id}", response_model=UserResponse)
async def checkout(
    plan_id: str,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> UserResponse:
    valid = {p["id"] for p in PLANS}
    if plan_id not in valid:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Plan inconnu")

    s = get_settings()
    tenant = store.tenants.get(user.tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant introuvable")

    # En prod : créer une session Stripe Checkout et rediriger ; le plan n'est activé qu'au webhook.
    if s.stripe_secret_key:
        logger.info("Création session Stripe Checkout pour %s -> %s", user.email, plan_id)
        # ... appel Stripe ici ...
    # MVP / dev : activation directe pour dérouler le parcours.
    tenant.plan = plan_id
    store.tenants.update(tenant)
    return _to_response(user, store)


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    """Réception des événements Stripe (signature à vérifier en prod)."""
    payload = await request.body()
    logger.info("Webhook Stripe reçu (%d octets)", len(payload))
    # En prod : vérifier la signature (STRIPE_WEBHOOK_SECRET) puis traiter
    # checkout.session.completed / customer.subscription.updated/deleted.
    return {"received": True}

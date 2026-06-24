"""M10 — Facturation Stripe (Checkout + webhook signé), avec repli stub sans clé.

- Si STRIPE_SECRET_KEY est configurée : crée une vraie session Stripe Checkout et renvoie son URL ;
  le plan n'est activé qu'à la réception du webhook signé `checkout.session.completed`.
- Sinon (dev/test) : active le plan directement pour dérouler le parcours.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.auth import _to_response
from app.core.config import get_settings
from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.models.schemas import UserResponse
from app.repositories.store import AppStore, get_store
from app.services import audit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])

PLANS = [
    {"id": "free", "price": 0, "markets": 1, "features": ["signaux limités", "alertes basiques"]},
    {"id": "starter", "price": 29, "markets": 3, "features": ["signaux illimités", "alertes multicanal"]},
    {"id": "pro", "price": 79, "markets": 999, "features": ["tous marchés", "backtesting", "AI Copilot"]},
    {"id": "elite", "price": 199, "markets": 999, "features": ["API", "copy-trading", "exécution auto"]},
    {"id": "enterprise", "price": 0, "markets": 999, "features": ["white-label", "SLA dédié", "multi-comptes avancé", "sur devis"]},
]
_PRICE_ENV = {"starter": "stripe_price_starter"}


@router.get("/plans")
async def plans() -> list[dict]:
    return PLANS


@router.post("/checkout/{plan_id}")
async def checkout(
    plan_id: str,
    request: Request,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    if plan_id not in {p["id"] for p in PLANS}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Plan inconnu")

    s = get_settings()
    tenant = store.tenants.get(user.tenant_id)
    if tenant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tenant introuvable")

    # --- Mode Stripe réel ---
    if s.stripe_secret_key and plan_id != "free":
        try:
            import stripe

            stripe.api_key = s.stripe_secret_key
            price_id = getattr(s, _PRICE_ENV.get(plan_id, ""), "") or ""
            base = str(request.base_url).rstrip("/")
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=f"{base}/dashboard?upgrade=success",
                cancel_url=f"{base}/settings?upgrade=cancel",
                client_reference_id=user.tenant_id,
                metadata={"tenant_id": user.tenant_id, "plan": plan_id},
            )
            audit.record("billing.checkout_created", actor=user.email, tenant_id=user.tenant_id, detail=plan_id)
            return {"mode": "stripe", "checkout_url": session.url}
        except Exception as exc:  # noqa: BLE001
            logger.error("Création session Stripe échouée (%s)", exc)
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Erreur Stripe") from exc

    # --- Repli dev/test : activation directe ---
    tenant.plan = plan_id
    store.tenants.update(tenant)
    audit.record("billing.plan_changed", actor=user.email, tenant_id=user.tenant_id, detail=f"-> {plan_id} (stub)")
    return {"mode": "stub", "user": _to_response(user, store).model_dump()}


@router.post("/webhook")
async def stripe_webhook(request: Request) -> dict:
    """Réception des événements Stripe avec vérification de signature."""
    s = get_settings()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    if not (s.stripe_secret_key and s.stripe_webhook_secret):
        # Pas de Stripe configuré : on ignore proprement.
        return {"received": True, "mode": "noop"}

    try:
        import stripe

        event = stripe.Webhook.construct_event(payload, sig, s.stripe_webhook_secret)
    except Exception as exc:  # noqa: BLE001 — signature invalide ou payload corrompu
        logger.warning("Webhook Stripe rejeté (%s)", exc)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Signature invalide") from exc

    if event["type"] == "checkout.session.completed":
        data = event["data"]["object"]
        tenant_id = (data.get("metadata") or {}).get("tenant_id") or data.get("client_reference_id")
        plan = (data.get("metadata") or {}).get("plan", "starter")
        if tenant_id:
            store = get_store()
            tenant = store.tenants.get(tenant_id)
            if tenant:
                tenant.plan = plan
                store.tenants.update(tenant)
                audit.record("billing.plan_activated", tenant_id=tenant_id, detail=f"-> {plan} (stripe)")

    return {"received": True}

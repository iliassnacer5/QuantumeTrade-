"""Marketplace (Phase 4) — annonces, achats, et clés API développeur payantes.

Navigation/achat : tout utilisateur authentifié. Vendre : plan Pro+ (marketplace_sell).
Clés API dev/institutionnelles : plan Elite (api_access).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import current_user, store_dep
from app.core.plans import require_feature
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import audit, marketplace_service as mkt

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


class ListingRequest(BaseModel):
    title: str
    kind: str = "strategy"  # strategy | agent
    price: float = 0.0
    description: str = ""
    config: dict = {}


class ApiKeyRequest(BaseModel):
    label: str = "default"


# ---------- Annonces ----------
@router.get("/listings")
async def listings(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return mkt.list_listings(store)


@router.post("/listings", status_code=status.HTTP_201_CREATED)
async def create_listing(
    body: ListingRequest,
    user: User = Depends(require_feature("marketplace_sell")),
    store: AppStore = Depends(store_dep),
) -> dict:
    try:
        listing = mkt.create_listing(
            store, user.tenant_id, title=body.title, kind=body.kind,
            price=body.price, description=body.description, config=body.config,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    audit.record("marketplace.listing_created", actor=user.email, tenant_id=user.tenant_id, detail=body.title)
    return mkt._public_listing(listing)


@router.post("/listings/{listing_id}/buy")
async def buy(
    listing_id: str,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    try:
        result = mkt.buy_listing(store, user.tenant_id, listing_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    audit.record("marketplace.purchase", actor=user.email, tenant_id=user.tenant_id, detail=listing_id)
    return result


@router.get("/purchases")
async def purchases(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return mkt.my_purchases(store, user.tenant_id)


# ---------- Clés API développeur (Elite) ----------
@router.get("/api-keys")
async def api_keys(
    user: User = Depends(require_feature("api_access")),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return mkt.list_api_keys(store, user.tenant_id)


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyRequest,
    user: User = Depends(require_feature("api_access")),
    store: AppStore = Depends(store_dep),
) -> dict:
    key = mkt.issue_api_key(store, user.tenant_id, body.label)
    audit.record("marketplace.api_key_issued", actor=user.email, tenant_id=user.tenant_id, detail=key["prefix"])
    return key


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user: User = Depends(require_feature("api_access")),
    store: AppStore = Depends(store_dep),
) -> dict:
    if not mkt.revoke_api_key(store, user.tenant_id, key_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Clé introuvable")
    return {"revoked": True}

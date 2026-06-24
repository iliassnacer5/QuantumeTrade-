"""White-label / branding (Phase 5).

- Lecture du branding : tout membre du tenant.
- Modification (nom, couleur, logo, domaine perso) : plan Enterprise (white_label).
- Résolution publique par domaine : non authentifiée (sert le rendu white-label côté client).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import current_user, store_dep
from app.core.plans import require_feature
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import audit, branding_service

router = APIRouter(prefix="/api/branding", tags=["branding"])


class BrandingRequest(BaseModel):
    brand_name: str | None = None
    primary_color: str | None = None
    logo_url: str | None = None
    custom_domain: str | None = None


@router.get("")
async def get_branding(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    return branding_service.get_branding(store, user.tenant_id)


@router.put("")
async def set_branding(
    body: BrandingRequest,
    user: User = Depends(require_feature("white_label")),
    store: AppStore = Depends(store_dep),
) -> dict:
    result = branding_service.set_branding(
        store, user.tenant_id, brand_name=body.brand_name, primary_color=body.primary_color,
        logo_url=body.logo_url, custom_domain=body.custom_domain,
    )
    audit.record("branding.updated", actor=user.email, tenant_id=user.tenant_id, detail=result.get("custom_domain") or "")
    return result


@router.get("/resolve")
async def resolve(domain: str, store: AppStore = Depends(store_dep)) -> dict:
    """Résolution publique du branding pour un domaine personnalisé (white-label)."""
    b = branding_service.resolve_by_domain(store, domain)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Domaine non configuré")
    return b

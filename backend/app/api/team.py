"""Gestion d'équipe / multi-utilisateurs (Phase 3) — réservé au plan Pro+.

Plusieurs utilisateurs partagent un même `tenant` (compte facturé). Le propriétaire peut lister les
membres et inviter un collègue (création d'un compte sous le même tenant avec un mot de passe
provisoire). Le plan étant porté par le tenant, les membres héritent des mêmes droits.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import current_user, store_dep
from app.core.plans import plan_of, require_feature
from app.core.security import hash_password
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import audit

router = APIRouter(prefix="/api/team", tags=["team"])

# Multi-comptes avancé (Phase 5) : nombre de sièges par plan.
SEAT_LIMITS = {"pro": 5, "elite": 20, "enterprise": 1000}


class InviteRequest(BaseModel):
    email: str
    full_name: str | None = None


def _member(u: User, owner_id: str) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "role": "owner" if u.id == owner_id else "member",
        "onboarded": u.onboarded,
    }


@router.get("")
async def list_members(
    user: User = Depends(require_feature("team")),
    store: AppStore = Depends(store_dep),
) -> dict:
    members = store.users.list_by_tenant(user.tenant_id)
    # Le membre le plus ancien est considéré propriétaire.
    owner = min(members, key=lambda m: m.created_at, default=user)
    return {
        "plan": plan_of(user, store),
        "members": [_member(m, owner.id) for m in sorted(members, key=lambda m: m.created_at)],
    }


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    body: InviteRequest,
    user: User = Depends(require_feature("team")),
    store: AppStore = Depends(store_dep),
) -> dict:
    # Limite de sièges selon le plan (multi-comptes avancé).
    limit = SEAT_LIMITS.get(plan_of(user, store), 1)
    if len(store.users.list_by_tenant(user.tenant_id)) >= limit:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"Limite de {limit} sièges atteinte pour votre plan. Passez à un plan supérieur.",
        )
    if store.users.get_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Un compte existe déjà avec cet email")
    temp_password = secrets.token_urlsafe(9)
    try:
        member = store.users.create(
            tenant_id=user.tenant_id,
            email=str(body.email),
            password_hash=hash_password(temp_password),
            full_name=body.full_name,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    audit.record("team.member_invited", actor=user.email, tenant_id=user.tenant_id, detail=str(body.email))
    # Le mot de passe provisoire est renvoyé une seule fois (à transmettre au membre).
    return {"member": _member(member, user.id), "temp_password": temp_password}

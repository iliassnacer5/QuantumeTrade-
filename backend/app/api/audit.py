"""Route de consultation du journal d'audit (limité au tenant courant)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import current_user
from app.models.entities import User
from app.services import audit as audit_service

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
async def list_audit(limit: int = 100, user: User = Depends(current_user)) -> list[dict]:
    return audit_service.recent(tenant_id=user.tenant_id, limit=limit)

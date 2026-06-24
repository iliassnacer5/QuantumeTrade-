"""KYC / AML (Phase 4) — prérequis légal pour l'exécution réelle.

Démo : la soumission est auto-vérifiée si les champs requis sont fournis. En production, brancher un
fournisseur KYC/AML (Onfido, Sumsub…) et passer le statut à 'verified' via webhook.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import audit, execution_service

router = APIRouter(prefix="/api/kyc", tags=["kyc"])


class KycRequest(BaseModel):
    legal_name: str
    country: str
    doc_id: str


@router.get("")
async def status(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    return execution_service.kyc_status(store, user.tenant_id)


@router.post("")
async def submit(
    body: KycRequest,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    rec = execution_service.submit_kyc(
        store, user.tenant_id, legal_name=body.legal_name, country=body.country, doc_id=body.doc_id
    )
    audit.record("kyc.submitted", actor=user.email, tenant_id=user.tenant_id, detail=rec["status"])
    return {"status": rec["status"]}

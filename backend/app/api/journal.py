"""Journal de trading & apprentissage (M9) — Phase 3.

Réservé au plan Pro+. Enregistrement auto des signaux (à la génération), clôture manuelle des trades
(issue + P&L), explication IA post-mortem, et exposition des multiplicateurs de pondération que le
Master applique (boucle de feedback).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import store_dep
from app.core.plans import require_feature
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import journal_service

router = APIRouter(prefix="/api/journal", tags=["journal"])


class CloseRequest(BaseModel):
    outcome: str  # win | loss | breakeven
    pnl: float | None = None


@router.get("")
async def list_entries(
    user: User = Depends(require_feature("journal")),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return journal_service.recent_entries(store, user.tenant_id, limit=200)


@router.get("/insights")
async def insights(
    user: User = Depends(require_feature("journal")),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Statistiques + apprentissage : fiabilité par agent et volume de trades appris."""
    from app.agents.journal import reliability_report

    entries = journal_service.recent_entries(store, user.tenant_id, limit=500)
    report = reliability_report(entries)
    learned = sum(1 for e in entries if e.get("outcome") in ("win", "loss"))
    return {
        "stats": journal_service.stats(entries),
        "weight_multipliers": journal_service.compute_multipliers(store, user.tenant_id),
        "reliability": report,            # détail par agent (réussite, volume, multiplicateur)
        "trades_learned": learned,        # nombre de trades clôturés qui nourrissent l'apprentissage
    }


@router.post("/auto-resolve")
async def auto_resolve(
    user: User = Depends(require_feature("journal")),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Force la résolution des signaux ouverts (sinon fait automatiquement en arrière-plan)."""
    resolved = await journal_service.auto_resolve(store, user.tenant_id)
    return {"resolved": resolved}


@router.post("/{entry_id}/close")
async def close_trade(
    entry_id: str,
    body: CloseRequest,
    user: User = Depends(require_feature("journal")),
    store: AppStore = Depends(store_dep),
) -> dict:
    try:
        updated = journal_service.close_trade(store, user.tenant_id, entry_id, body.outcome, body.pnl)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrée de journal introuvable")
    return updated


@router.post("/{entry_id}/explain")
async def explain(
    entry_id: str,
    user: User = Depends(require_feature("journal")),
    store: AppStore = Depends(store_dep),
) -> dict:
    entry = store.journal.get(user.tenant_id, entry_id)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrée de journal introuvable")
    explanation = await journal_service.explain_trade(entry)
    return {"id": entry_id, "explanation": explanation}

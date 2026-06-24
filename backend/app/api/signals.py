"""Routes des signaux : génération à la demande + historique (isolé par tenant)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import current_user, store_dep
from app.models.entities import User
from app.models.schemas import GenerateSignalRequest
from app.models.signal import SignalCard
from app.repositories.store import AppStore
from app.services import risk_service, signal_service

router = APIRouter(prefix="/api/signals", tags=["signals"])

# Gating par plan (cf. grille tarifaire) : Free = 1 marché.
_PLAN_MARKETS = {"free": 1, "starter": 3, "pro": 999, "elite": 999, "enterprise": 999}


@router.post("/generate", response_model=SignalCard)
async def generate(
    body: GenerateSignalRequest,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> SignalCard:
    tenant = store.tenants.get(user.tenant_id)
    plan = tenant.plan if tenant else "free"
    allowed = _PLAN_MARKETS.get(plan, 1)
    base = body.asset.split("/")[0]
    distinct_markets = {s.payload.get("asset", "").split("/")[0] for s in store.signals.list_for_tenant(user.tenant_id, 1000)}
    if base not in distinct_markets and len(distinct_markets) >= allowed:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            f"Plan '{plan}' limité à {allowed} marché(s). Passez à un plan supérieur.",
        )

    # Garde-fous de risque (exposition / signaux quotidiens) — protection du capital.
    ok, reason = risk_service.check_can_generate(user, store)
    if not ok:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, reason)

    return await signal_service.generate_for_user(
        user, store, asset=body.asset, timeframe=body.timeframe, notify=body.notify
    )


@router.get("/scan")
async def scan(
    asset_class: str | None = None,
    timeframe: str = "1h",
    limit: int = 20,
    high_conviction_only: bool = False,
    _user: User = Depends(current_user),
) -> dict:
    """Scanner de marché : classe les symboles par conviction (flag haute-conviction ADX>25)."""
    results = await signal_service.scan_market(
        asset_class=asset_class, timeframe=timeframe, limit=min(limit, 30),
        high_conviction_only=high_conviction_only,
    )
    return {
        "count": len(results),
        "high_conviction": sum(1 for r in results if r["high_conviction"]),
        "results": results,
    }


@router.get("")
async def list_signals(
    limit: int = 50,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    items = store.signals.list_for_tenant(user.tenant_id, limit)
    out = []
    for s in items:
        payload = dict(s.payload)
        payload["id"] = s.id
        out.append(payload)
    return out

"""Routes des signaux : génération à la demande + historique (isolé par tenant)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from pydantic import BaseModel

from app.core.deps import current_user, store_dep
from app.core.plans import require_feature
from app.models.entities import User
from app.models.schemas import GenerateSignalRequest
from app.models.signal import SignalCard
from app.repositories.store import AppStore
from app.services import risk_service, signal_service

router = APIRouter(prefix="/api/signals", tags=["signals"])


class VerifyRequest(BaseModel):
    symbol: str
    timeframe: str = "swing"
    direction: str = "HOLD"
    confidence: int = 0
    consensus_pct: int = 0
    risk_reward: float = 0.0
    mtf_aligned: int = 0
    mtf_total: int = 0
    adx: float | None = None

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


@router.get("/daily-picks")
async def daily_picks(
    refresh: bool = False,
    user: User = Depends(require_feature("backtesting")),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Sélection du jour : trades haute-conviction confirmés par backtest, par marché (mis en cache)."""
    from datetime import UTC, datetime

    today = datetime.now(UTC).date().isoformat()
    cached = store.records.get("daily_picks", today)
    if cached and not refresh:
        return cached
    picks = await signal_service.daily_picks()
    return store.records.put(
        "daily_picks", today, {"date": today, "picks": picks, "generated_at": datetime.now(UTC).isoformat()},
    )


@router.post("/verify")
async def verify(
    body: VerifyRequest,
    user: User = Depends(require_feature("backtesting")),
) -> dict:
    """Vérifie la fiabilité d'un signal : backtest auto de la paire + verdict checklist."""
    return await signal_service.verify_signal(
        body.symbol, body.timeframe,
        confidence=body.confidence, consensus_pct=body.consensus_pct, risk_reward=body.risk_reward,
        mtf_aligned=body.mtf_aligned, mtf_total=body.mtf_total, adx=body.adx, direction=body.direction,
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


@router.delete("")
async def clear_signals(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Vide l'historique des signaux du tenant (repartir propre)."""
    deleted = store.signals.clear_for_tenant(user.tenant_id)
    return {"deleted": deleted}


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

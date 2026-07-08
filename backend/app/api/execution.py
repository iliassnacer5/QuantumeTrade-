"""Exécution broker (M8, Phase 4) — réservé Elite (auto_execution). Mode papier par défaut.

Garde-fous : clés chiffrées (jamais renvoyées), exécution réelle conditionnée au KYC vérifié.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import current_user, store_dep
from app.core.plans import plan_allows, plan_of
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import audit, execution_service

router = APIRouter(prefix="/api/execution", tags=["execution"])


def _require_live_allowed(user: User, store: AppStore) -> None:
    """Le trading RÉEL exige le plan Elite (auto_execution). Le KYC est vérifié par connect_broker.
    Le mode papier est libre (apprentissage sans risque)."""
    if not plan_allows(plan_of(user, store), "auto_execution"):
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            "Le trading réel est réservé au plan Elite. Le mode papier reste gratuit.",
        )


class ConnectRequest(BaseModel):
    broker: str = "paper"  # paper | alpaca
    api_key: str = ""
    api_secret: str = ""
    mode: str = "paper"  # paper | live


class OrderRequest(BaseModel):
    conn_id: str
    symbol: str
    side: str  # buy | sell
    qty: float
    stop_loss: float | None = None
    take_profit: float | None = None


@router.post("/brokers", status_code=status.HTTP_201_CREATED)
async def connect(
    body: ConnectRequest,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    if body.mode == "live":
        _require_live_allowed(user, store)
    try:
        conn = execution_service.connect_broker(
            store, user.tenant_id, broker=body.broker, api_key=body.api_key,
            api_secret=body.api_secret, mode=body.mode,
        )
    except execution_service.ExecutionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    audit.record("execution.broker_connected", actor=user.email, tenant_id=user.tenant_id, detail=f"{body.broker}/{conn['mode']}")
    return conn


@router.get("/brokers")
async def brokers(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return execution_service.list_connections(store, user.tenant_id)


@router.delete("/brokers/{conn_id}")
async def revoke(
    conn_id: str,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    if not execution_service.revoke_connection(store, user.tenant_id, conn_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connexion introuvable")
    audit.record("execution.broker_revoked", actor=user.email, tenant_id=user.tenant_id, detail=conn_id)
    return {"revoked": True}


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def place_order(
    body: OrderRequest,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    # Un ordre sur une connexion RÉELLE exige Elite + KYC ; le papier est libre.
    conn = next((c for c in execution_service.list_connections(store, user.tenant_id) if c["id"] == body.conn_id), None)
    if conn and conn.get("mode") == "live":
        _require_live_allowed(user, store)
    try:
        order = await execution_service.place_order(
            store, user.tenant_id, conn_id=body.conn_id, symbol=body.symbol, side=body.side,
            qty=body.qty, stop_loss=body.stop_loss, take_profit=body.take_profit,
        )
    except execution_service.ExecutionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    audit.record("execution.order_placed", actor=user.email, tenant_id=user.tenant_id, detail=f"{order['side']} {order['qty']} {order['symbol']} ({order['mode']})")
    return order


@router.get("/orders")
async def orders(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return execution_service.list_orders(store, user.tenant_id)


@router.post("/orders/{order_id}/close")
async def close_order(
    order_id: str,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Clôture manuelle d'une position papier au prix du marché (P&L réalisé immédiat)."""
    try:
        result = await execution_service.close_order_manual(store, user.tenant_id, order_id)
    except execution_service.ExecutionError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    audit.record("execution.order_closed_manual", actor=user.email, tenant_id=user.tenant_id,
                 detail=f"{result['outcome']} {result['symbol']} pnl={result.get('realized_pnl')}")
    return result


@router.post("/orders/{order_id}/check")
async def check_order(
    order_id: str,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Vérifie si le trade papier a gagné (TP) / perdu (SL) / est encore ouvert, depuis l'entrée."""
    try:
        result = await execution_service.check_order_outcome(store, user.tenant_id, order_id)
    except execution_service.ExecutionError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    if result.get("outcome") in {"won", "lost"}:
        audit.record("execution.order_closed", actor=user.email, tenant_id=user.tenant_id,
                     detail=f"{result['outcome']} {result['symbol']} pnl={result.get('realized_pnl')}")
    return result

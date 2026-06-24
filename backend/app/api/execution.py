"""Exécution broker (M8, Phase 4) — réservé Elite (auto_execution). Mode papier par défaut.

Garde-fous : clés chiffrées (jamais renvoyées), exécution réelle conditionnée au KYC vérifié.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.deps import store_dep
from app.core.plans import require_feature
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import audit, execution_service

router = APIRouter(prefix="/api/execution", tags=["execution"])


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


@router.post("/brokers", status_code=status.HTTP_201_CREATED)
async def connect(
    body: ConnectRequest,
    user: User = Depends(require_feature("auto_execution")),
    store: AppStore = Depends(store_dep),
) -> dict:
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
    user: User = Depends(require_feature("auto_execution")),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return execution_service.list_connections(store, user.tenant_id)


@router.delete("/brokers/{conn_id}")
async def revoke(
    conn_id: str,
    user: User = Depends(require_feature("auto_execution")),
    store: AppStore = Depends(store_dep),
) -> dict:
    if not execution_service.revoke_connection(store, user.tenant_id, conn_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connexion introuvable")
    audit.record("execution.broker_revoked", actor=user.email, tenant_id=user.tenant_id, detail=conn_id)
    return {"revoked": True}


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def place_order(
    body: OrderRequest,
    user: User = Depends(require_feature("auto_execution")),
    store: AppStore = Depends(store_dep),
) -> dict:
    try:
        order = await execution_service.place_order(
            store, user.tenant_id, conn_id=body.conn_id, symbol=body.symbol, side=body.side, qty=body.qty
        )
    except execution_service.ExecutionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    audit.record("execution.order_placed", actor=user.email, tenant_id=user.tenant_id, detail=f"{order['side']} {order['qty']} {order['symbol']} ({order['mode']})")
    return order


@router.get("/orders")
async def orders(
    user: User = Depends(require_feature("auto_execution")),
    store: AppStore = Depends(store_dep),
) -> list[dict]:
    return execution_service.list_orders(store, user.tenant_id)

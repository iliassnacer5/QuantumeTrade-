"""WebSocket temps réel : flux des signaux du tenant (auth par token en query param)."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import TokenError, decode_access_token
from app.realtime.hub import get_hub
from app.repositories.store import get_store

router = APIRouter()


@router.websocket("/ws/signals")
async def ws_signals(websocket: WebSocket, token: str = "") -> None:
    # Authentification : le navigateur passe ?token=<jwt>
    try:
        payload = decode_access_token(token)
    except TokenError:
        await websocket.close(code=4401)
        return

    tenant_id = payload.get("tid", "")
    user = get_store().users.get(payload.get("sub", ""))
    if user is None or user.tenant_id != tenant_id:
        await websocket.close(code=4401)
        return

    hub = get_hub()
    await hub.connect(tenant_id, websocket)
    try:
        await websocket.send_json({"type": "connected", "tenant_id": tenant_id})
        # Snapshot initial des prix live -> l'UI affiche le ticker immédiatement (sans attendre une clôture).
        from app.realtime import market_stream

        for candle in market_stream.latest_snapshot():
            await websocket.send_json({"type": "candle", "data": candle})
        while True:
            # On garde la connexion ouverte ; les clients peuvent envoyer des pings.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(tenant_id, websocket)

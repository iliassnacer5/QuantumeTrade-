"""Hub de diffusion WebSocket par tenant (isolation multi-tenant des flux)."""

from __future__ import annotations

import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionHub:
    def __init__(self) -> None:
        self._conns: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, tenant_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._conns[tenant_id].add(ws)

    async def disconnect(self, tenant_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._conns[tenant_id].discard(ws)

    async def broadcast(self, tenant_id: str, message: dict) -> None:
        """Envoie un message JSON à toutes les connexions d'un tenant (best-effort)."""
        async with self._lock:
            targets = list(self._conns.get(tenant_id, set()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001 — connexion morte
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    self._conns[tenant_id].discard(ws)

    async def broadcast_all(self, message: dict) -> None:
        """Diffuse à TOUTES les connexions (données marché publiques, non liées à un tenant)."""
        async with self._lock:
            targets = [(tid, ws) for tid, conns in self._conns.items() for ws in conns]
        dead: list[tuple[str, WebSocket]] = []
        for tid, ws in targets:
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001 — connexion morte
                dead.append((tid, ws))
        if dead:
            async with self._lock:
                for tid, ws in dead:
                    self._conns[tid].discard(ws)


_hub: ConnectionHub | None = None


def get_hub() -> ConnectionHub:
    global _hub
    if _hub is None:
        _hub = ConnectionHub()
    return _hub

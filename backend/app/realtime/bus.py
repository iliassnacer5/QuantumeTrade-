"""Bus de diffusion des signaux — Redis pub/sub (multi-instance) avec repli en mémoire.

- Si REDIS_URL est joignable -> publication sur le canal `signals:<tenant>` ; un abonné de fond
  (par instance) reçoit et rediffuse vers les WebSockets locales -> scaling horizontal.
- Sinon -> diffusion directe via le hub en mémoire (dev / tests / mono-instance).
"""

from __future__ import annotations

import asyncio
import json
import logging

from app.core.config import get_settings
from app.realtime.hub import get_hub

logger = logging.getLogger(__name__)

_redis = None
_enabled = False
_sub_task: asyncio.Task | None = None


async def init_bus() -> None:
    """Initialise le bus Redis si disponible (appelé au démarrage de l'app)."""
    global _redis, _enabled, _sub_task
    s = get_settings()
    if not s.redis_url:
        return
    try:
        import redis.asyncio as aioredis

        _redis = aioredis.from_url(s.redis_url, decode_responses=True)
        await _redis.ping()
        _enabled = True
        _sub_task = asyncio.create_task(_subscribe())
        logger.info("Bus Redis actif (%s)", s.redis_url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis indisponible (%s) -> bus en mémoire", exc)
        _enabled = False
        _redis = None


async def shutdown_bus() -> None:
    global _sub_task
    if _sub_task:
        _sub_task.cancel()
        _sub_task = None
    if _redis:
        await _redis.aclose()


async def _subscribe() -> None:
    pubsub = _redis.pubsub()
    await pubsub.psubscribe("signals:*")
    async for msg in pubsub.listen():
        if msg.get("type") != "pmessage":
            continue
        channel = msg["channel"]
        tenant_id = channel.split(":", 1)[1]
        try:
            data = json.loads(msg["data"])
        except (ValueError, TypeError):
            continue
        await get_hub().broadcast(tenant_id, data)


async def publish(tenant_id: str, message: dict) -> None:
    """Diffuse un message aux clients d'un tenant (via Redis si actif, sinon hub local)."""
    if _enabled and _redis is not None:
        await _redis.publish(f"signals:{tenant_id}", json.dumps(message))
    else:
        await get_hub().broadcast(tenant_id, message)


def is_redis_enabled() -> bool:
    return _enabled

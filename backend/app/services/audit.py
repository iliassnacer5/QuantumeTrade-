"""Journal d'audit de sécurité.

Enregistre les événements sensibles (inscription, connexion, échec de connexion, changement de
plan, génération de signal, activation MFA). Persistance SQL en prod, mémoire sinon. Toujours
journalisé via le logger `audit`.
"""

from __future__ import annotations

import logging
import uuid
from collections import deque
from datetime import UTC, datetime

from app.core.config import get_settings

logger = logging.getLogger("audit")

# Buffer mémoire (mode in-memory ou consultation rapide).
_buffer: deque[dict] = deque(maxlen=1000)
_sm = None


def _sessionmaker():
    global _sm
    if _sm is None:
        from app.repositories.sql import make_engine_sessionmaker

        _, _sm = make_engine_sessionmaker(get_settings().database_url_sync)
    return _sm


def record(action: str, *, actor: str | None = None, tenant_id: str | None = None, detail: str = "", ip: str | None = None) -> None:
    entry = {
        "id": str(uuid.uuid4()),
        "action": action,
        "actor": actor,
        "tenant_id": tenant_id,
        "detail": detail,
        "ip": ip,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _buffer.append(entry)
    logger.info("AUDIT %s actor=%s tenant=%s ip=%s %s", action, actor, tenant_id, ip, detail)

    # Persistance SQL best-effort.
    if not get_settings().use_in_memory_db:
        try:
            from app.models.db import AuditORM

            sm = _sessionmaker()
            with sm() as s:
                s.add(
                    AuditORM(
                        id=entry["id"],
                        tenant_id=tenant_id,
                        actor=actor,
                        action=action,
                        detail=detail,
                        ip=ip,
                    )
                )
                s.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Persistance audit échouée (%s)", exc)


def recent(tenant_id: str | None = None, limit: int = 100) -> list[dict]:
    items = [e for e in reversed(_buffer) if tenant_id is None or e["tenant_id"] == tenant_id]
    return items[:limit]

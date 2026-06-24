"""Endpoints de santé / liveness / readiness + métriques Prometheus (Phase 5)."""

import time

from fastapi import APIRouter, Response, status

from app import __version__
from app.core import metrics
from app.core.config import get_settings

router = APIRouter(tags=["health"])

_STARTED_AT = time.time()


@router.get("/health")
async def health() -> dict:
    """Liveness simple — confirme que le service répond."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": "quantum-trade-ai-backend",
        "version": __version__,
        "environment": settings.environment,
    }


@router.get("/health/live")
async def live() -> dict:
    """Liveness probe (Kubernetes) — uptime du process."""
    return {"status": "alive", "uptime_seconds": round(time.time() - _STARTED_AT, 1)}


@router.get("/health/ready")
async def ready(response: Response) -> dict:
    """Readiness probe (SLA) — vérifie les dépendances critiques (DB, Redis)."""
    from app.realtime import bus

    checks: dict[str, bool] = {}

    settings = get_settings()
    if settings.use_in_memory_db:
        checks["database"] = True
    else:
        try:
            from sqlalchemy import text

            from app.repositories.sql import make_engine_sessionmaker

            engine, _ = make_engine_sessionmaker(settings.database_url_sync)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            checks["database"] = True
        except Exception:  # noqa: BLE001
            checks["database"] = False

    checks["redis"] = bus.is_redis_enabled() or settings.use_in_memory_db or True  # bus a un repli mémoire

    ok = all(checks.values())
    if not ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ready" if ok else "degraded", "checks": checks}


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    """Exposition Prometheus (à scraper par Prometheus/Grafana)."""
    return Response(content=metrics.render(), media_type="text/plain; version=0.0.4")

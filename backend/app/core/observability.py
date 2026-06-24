"""Middleware d'observabilité — Phase 5.

- attribue un X-Request-ID à chaque requête (tracing/corrélation des logs) ;
- mesure la latence et compte les requêtes par méthode/route/statut (métriques Prometheus) ;
- journalise de façon structurée (request_id, méthode, route, statut, durée).

Initialise aussi Sentry si SENTRY_DSN est fourni (capture d'erreurs ; optionnel, no-op sinon).
"""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core import metrics

logger = logging.getLogger("app.access")

metrics.register("http_requests_total", "counter", "Nombre total de requêtes HTTP.")
metrics.register("http_request_duration_seconds", "histogram", "Latence des requêtes HTTP (s).")


def _route(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration = time.perf_counter() - start
            route = _route(request)
            metrics.inc("http_requests_total", method=request.method, route=route, status=str(status_code))
            metrics.observe("http_request_duration_seconds", duration, method=request.method, route=route)
            logger.info(
                "%s %s -> %s (%.1fms) rid=%s",
                request.method, route, status_code, duration * 1000, request_id,
            )


def init_sentry() -> bool:
    """Active Sentry si SENTRY_DSN est configuré. Retourne True si activé."""
    from app.core.config import get_settings

    dsn = getattr(get_settings(), "sentry_dsn", "") or ""
    if not dsn:
        return False
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.1)
        return True
    except Exception as exc:  # noqa: BLE001 — Sentry optionnel
        logging.getLogger(__name__).warning("Sentry non initialisé (%s)", exc)
        return False

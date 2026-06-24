"""Rate limiting léger en mémoire (fenêtre glissante par IP).

Sans dépendance externe. Limite globale souple + limite stricte sur les routes d'authentification
(anti brute-force). En production multi-instance, on déléguerait à Redis ; ici suffisant et testable.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings

# (préfixe, bucket, limite, fenêtre_secondes)
_RULES = [
    ("/api/auth/login", "auth_login", 10, 60),
    ("/api/auth/register", "auth_register", 5, 60),
]
_DEFAULT = ("default", 120, 60)  # 120 req / min / IP par défaut


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:  # noqa: ANN001
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _rule_for(self, path: str) -> tuple[str, int, int]:
        for prefix, bucket, limit, window in _RULES:
            if path.startswith(prefix):
                return bucket, limit, window
        return _DEFAULT

    async def dispatch(self, request: Request, call_next):  # noqa: ANN001
        if not get_settings().rate_limit_enabled:
            return await call_next(request)

        # On ne limite pas le WebSocket ni le health.
        path = request.url.path
        if path == "/health" or path.startswith("/ws"):
            return await call_next(request)

        bucket, limit, window = self._rule_for(path)
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{bucket}"

        now = time.time()
        dq = self._hits[key]
        while dq and dq[0] <= now - window:
            dq.popleft()
        if len(dq) >= limit:
            retry = int(window - (now - dq[0])) + 1
            return JSONResponse(
                {"detail": "Trop de requêtes, réessayez plus tard."},
                status_code=429,
                headers={"Retry-After": str(retry)},
            )
        dq.append(now)
        return await call_next(request)

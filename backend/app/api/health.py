"""Endpoints de santé / liveness / readiness."""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness probe — confirme que le service répond."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": "quantum-trade-ai-backend",
        "version": __version__,
        "environment": settings.environment,
    }

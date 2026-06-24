"""Point d'entrée de l'API FastAPI Quantum Trade AI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import (
    audit,
    auth,
    billing,
    health,
    market,
    onboarding,
    portfolio,
    risk,
    settings as settings_api,
    signals,
    ws,
    backtest,
    agents,
    plan,
    copilot,
    journal,
    team,
    execution,
    kyc,
    copytrading,
    marketplace,
    i18n,
    branding,
)
from app.core.config import get_settings
from app.core.observability import ObservabilityMiddleware, init_sentry
from app.core.ratelimit import RateLimitMiddleware

settings = get_settings()
logging.basicConfig(level=settings.log_level)
init_sentry()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Cycle de vie : init persistance (create_all en mode SQL) + bus Redis."""
    from app.realtime import bus
    from app.repositories.store import get_store

    get_store()
    await bus.init_bus()
    logging.getLogger(__name__).info(
        "Démarrage OK (in_memory=%s, redis=%s)",
        get_settings().use_in_memory_db,
        bus.is_redis_enabled(),
    )
    yield
    await bus.shutdown_bus()


app = FastAPI(
    title="Quantum Trade AI API",
    version=__version__,
    description="API de la plateforme de trading multi-agents IA. Aide à la décision, pas un conseil en investissement.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ObservabilityMiddleware)

# Routes
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(signals.router)
app.include_router(market.router)
app.include_router(portfolio.router)
app.include_router(risk.router)
app.include_router(settings_api.router)
app.include_router(billing.router)
app.include_router(audit.router)
app.include_router(ws.router)
app.include_router(backtest.router)
app.include_router(agents.router)
app.include_router(plan.router)
app.include_router(copilot.router)
app.include_router(journal.router)
app.include_router(team.router)
app.include_router(execution.router)
app.include_router(kyc.router)
app.include_router(copytrading.router)
app.include_router(marketplace.router)
app.include_router(i18n.router)
app.include_router(branding.router)


@app.get("/")
async def root() -> dict:
    return {"message": "Quantum Trade AI API", "docs": "/docs", "health": "/health"}

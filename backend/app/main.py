"""Point d'entrée de l'API FastAPI Quantum Trade AI."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import health
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Quantum Trade AI API",
    version=__version__,
    description="API de la plateforme de trading multi-agents IA. Aide à la décision, pas un conseil en investissement.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes (étendues phase par phase : auth, signals, billing, ws...)
app.include_router(health.router)


@app.get("/")
async def root() -> dict:
    return {"message": "Quantum Trade AI API", "docs": "/docs", "health": "/health"}

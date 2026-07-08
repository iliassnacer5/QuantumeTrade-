"""AI Copilot (M5) — endpoint chat contextuel en streaming (SSE) — Phase 3.

Réservé au plan Pro+. Diffuse la réponse token par token via Server-Sent Events ; le frontend
consomme le flux pour un rendu progressif. Une variante non-stream est fournie pour les clients
simples (mobile).
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.deps import store_dep
from app.core.plans import require_feature
from app.models.entities import User
from app.repositories.store import AppStore
from app.services import copilot_service

router = APIRouter(prefix="/api/copilot", tags=["copilot"])


class ChatRequest(BaseModel):
    asset: str | None = None  # indice optionnel : actif par défaut si la question ne cite aucun symbole
    message: str


@router.post("/chat")
async def chat(
    body: ChatRequest,
    user: User = Depends(require_feature("copilot")),
    store: AppStore = Depends(store_dep),
) -> StreamingResponse:
    """Réponse en streaming SSE. Chaque événement : `data: {"delta": "..."}`; fin : `data: [DONE]`."""

    async def event_gen():
        try:
            async for piece in copilot_service.answer_stream(user, store, body.asset, body.message):
                yield f"data: {json.dumps({'delta': piece})}\n\n"
        except Exception as exc:  # noqa: BLE001
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/ask")
async def ask(
    body: ChatRequest,
    user: User = Depends(require_feature("copilot")),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Variante non-streaming : agrège la réponse complète (utile pour mobile/clients simples)."""
    parts = [p async for p in copilot_service.answer_stream(user, store, body.asset, body.message)]
    return {"asset": body.asset, "answer": "".join(parts)}

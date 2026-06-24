"""Endpoints i18n (Phase 5) — catalogues de traduction pour le frontend/mobile."""

from __future__ import annotations

from fastapi import APIRouter, Header

from app.core import i18n

router = APIRouter(prefix="/api/i18n", tags=["i18n"])


@router.get("")
async def resolve(accept_language: str | None = Header(default=None)) -> dict:
    """Catalogue de la locale négociée (Accept-Language), avec repli français."""
    locale = i18n.normalize(accept_language)
    return {"locale": locale, "supported": list(i18n.SUPPORTED), "messages": i18n.catalog(locale)}


@router.get("/{locale}")
async def by_locale(locale: str) -> dict:
    norm = i18n.normalize(locale)
    return {"locale": norm, "supported": list(i18n.SUPPORTED), "messages": i18n.catalog(norm)}

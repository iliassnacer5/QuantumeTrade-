"""Dépendances FastAPI : récupération de l'utilisateur courant via JWT + isolation tenant."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import TokenError, decode_access_token
from app.models.entities import User
from app.repositories.store import AppStore, get_store

_bearer = HTTPBearer(auto_error=False)


def store_dep() -> AppStore:
    return get_store()


async def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    store: AppStore = Depends(store_dep),
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
    try:
        payload = decode_access_token(creds.credentials)
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    user = store.users.get(payload.get("sub", ""))
    if user is None or user.tenant_id != payload.get("tid"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Utilisateur introuvable")
    return user

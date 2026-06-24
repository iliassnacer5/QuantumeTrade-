"""Routes d'authentification : inscription, connexion, profil courant."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import current_user, store_dep
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import User
from app.models.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.repositories.store import AppStore

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_response(user: User, store: AppStore) -> UserResponse:
    tenant = store.tenants.get(user.tenant_id)
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        risk_profile=user.risk_profile,
        capital=user.capital,
        watchlist=user.watchlist,
        onboarded=user.onboarded,
        plan=tenant.plan if tenant else "free",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, store: AppStore = Depends(store_dep)) -> TokenResponse:
    if store.users.get_by_email(body.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email déjà enregistré")
    # Chaque inscription crée un tenant dédié (multi-tenant strict).
    tenant = store.tenants.create(name=body.email)
    user = store.users.create(
        tenant_id=tenant.id,
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
    )
    token = create_access_token(user.id, tenant_id=user.tenant_id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, store: AppStore = Depends(store_dep)) -> TokenResponse:
    user = store.users.get_by_email(body.email)
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Identifiants invalides")
    token = create_access_token(user.id, tenant_id=user.tenant_id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(current_user), store: AppStore = Depends(store_dep)) -> UserResponse:
    return _to_response(user, store)

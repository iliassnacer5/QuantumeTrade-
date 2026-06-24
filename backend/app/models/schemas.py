"""Schémas Pydantic pour les requêtes/réponses de l'API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.signal import Timeframe

# Validation email simple sans dépendance email-validator (suffisant pour le MVP).
_EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterRequest(BaseModel):
    email: str = Field(pattern=_EMAIL_RE)
    password: str = Field(min_length=8)
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: str = Field(pattern=_EMAIL_RE)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    risk_profile: str
    capital: float
    watchlist: list[str]
    onboarded: bool
    plan: str


class OnboardingRequest(BaseModel):
    risk_profile: str = Field(pattern="^(conservative|moderate|aggressive)$")
    capital: float = Field(gt=0)
    watchlist: list[str] = Field(default_factory=lambda: ["BTC/USDT"], max_length=20)


class GenerateSignalRequest(BaseModel):
    asset: str = "BTC/USDT"
    timeframe: Timeframe = Timeframe.SWING
    notify: bool = False

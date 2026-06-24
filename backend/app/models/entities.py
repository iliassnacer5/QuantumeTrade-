"""Entités de domaine (dataclasses) — indépendantes du moteur de persistance.

Les repositories (mémoire ou SQL) manipulent ces objets. Cela permet de faire tourner le MVP
en mémoire et de basculer vers PostgreSQL sans toucher la logique métier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Tenant:
    id: str
    name: str
    plan: str = "free"  # free | starter | pro | elite | enterprise
    created_at: datetime = field(default_factory=_now)


@dataclass
class User:
    id: str
    tenant_id: str
    email: str
    password_hash: str
    full_name: str | None = None
    mfa_enabled: bool = False
    risk_profile: str = "moderate"  # conservative | moderate | aggressive
    capital: float = 10000.0
    watchlist: list[str] = field(default_factory=lambda: ["BTC/USDT"])
    onboarded: bool = False
    created_at: datetime = field(default_factory=_now)


@dataclass
class StoredSignal:
    id: str
    tenant_id: str
    payload: dict  # SignalCard sérialisée
    created_at: datetime = field(default_factory=_now)

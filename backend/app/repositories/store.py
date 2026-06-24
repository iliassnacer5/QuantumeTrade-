"""Conteneur de dépendances applicatives (repositories partagés).

Choisit l'implémentation selon la configuration :
- `use_in_memory_db=true`  -> repositories en mémoire (MVP / tests, sans Postgres)
- `use_in_memory_db=false` -> repositories SQL (SQLAlchemy, Postgres en prod)

L'interface est identique dans les deux cas : le reste du code est agnostique du moteur.
"""

from __future__ import annotations

from typing import Protocol

from app.core.config import get_settings
from app.models.entities import StoredSignal, Tenant, User


# Contrats minimaux (documentation/typage ; les deux implémentations s'y conforment).
class _Users(Protocol):
    def create(self, *, tenant_id: str, email: str, password_hash: str, full_name: str | None) -> User: ...
    def get(self, user_id: str) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def update(self, user: User) -> User: ...


class _Tenants(Protocol):
    def create(self, name: str, plan: str = "free") -> Tenant: ...
    def get(self, tenant_id: str) -> Tenant | None: ...
    def update(self, tenant: Tenant) -> Tenant: ...


class _Signals(Protocol):
    def add(self, tenant_id: str, payload: dict) -> StoredSignal: ...
    def list_for_tenant(self, tenant_id: str, limit: int = 50) -> list[StoredSignal]: ...
    def get(self, signal_id: str) -> StoredSignal | None: ...


class _Market(Protocol):
    def upsert_ohlcv(self, symbol: str, timeframe: str, rows: list[dict]) -> int: ...
    def count(self, symbol: str, timeframe: str) -> int: ...


class AppStore:
    users: _Users
    tenants: _Tenants
    signals: _Signals
    market: _Market

    def __init__(self) -> None:
        settings = get_settings()
        if settings.use_in_memory_db:
            from app.repositories.memory import (
                SignalRepository,
                TenantRepository,
                UserRepository,
            )
            from app.repositories.sql import NoopMarketRepository

            self.users = UserRepository()
            self.tenants = TenantRepository()
            self.signals = SignalRepository()
            self.market = NoopMarketRepository()
        else:
            from app.repositories.sql import (
                SqlMarketRepository,
                SqlSignalRepository,
                SqlTenantRepository,
                SqlUserRepository,
                make_engine_sessionmaker,
            )

            _, sm = make_engine_sessionmaker(settings.database_url_sync)
            self.users = SqlUserRepository(sm)
            self.tenants = SqlTenantRepository(sm)
            self.signals = SqlSignalRepository(sm)
            self.market = SqlMarketRepository(sm)


_store: AppStore | None = None


def get_store() -> AppStore:
    global _store
    if _store is None:
        _store = AppStore()
    return _store


def reset_store() -> None:
    """Réinitialise l'état (utilisé par les tests)."""
    global _store
    _store = AppStore()


def set_store(store: AppStore) -> None:
    """Injecte un store spécifique (tests de la couche SQL)."""
    global _store
    _store = store

"""Conteneur de dépendances applicatives (repositories partagés + bus temps réel).

Singleton simple pour le MVP. En production, remplacer par injection + repositories SQL.
"""

from __future__ import annotations

from app.repositories.memory import SignalRepository, TenantRepository, UserRepository


class AppStore:
    def __init__(self) -> None:
        self.users = UserRepository()
        self.tenants = TenantRepository()
        self.signals = SignalRepository()


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

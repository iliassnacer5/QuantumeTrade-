"""Repositories en mémoire (MVP / tests). Thread-safe suffisant pour un process unique."""

from __future__ import annotations

import uuid

from app.models.entities import StoredSignal, Tenant, User
from app.backtest.schemas import BacktestReport


class UserRepository:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._by_email: dict[str, str] = {}

    def create(self, *, tenant_id: str, email: str, password_hash: str, full_name: str | None) -> User:
        email = email.lower()
        if email in self._by_email:
            raise ValueError("email déjà utilisé")
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
        )
        self._users[user.id] = user
        self._by_email[email] = user.id
        return user

    def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        uid = self._by_email.get(email.lower())
        return self._users.get(uid) if uid else None

    def update(self, user: User) -> User:
        self._users[user.id] = user
        return user


class TenantRepository:
    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}

    def create(self, name: str, plan: str = "free") -> Tenant:
        tenant = Tenant(id=str(uuid.uuid4()), name=name, plan=plan)
        self._tenants[tenant.id] = tenant
        return tenant

    def get(self, tenant_id: str) -> Tenant | None:
        return self._tenants.get(tenant_id)

    def update(self, tenant: Tenant) -> Tenant:
        self._tenants[tenant.id] = tenant
        return tenant


class SignalRepository:
    def __init__(self) -> None:
        self._signals: dict[str, StoredSignal] = {}

    def add(self, tenant_id: str, payload: dict) -> StoredSignal:
        sig = StoredSignal(id=str(uuid.uuid4()), tenant_id=tenant_id, payload=payload)
        self._signals[sig.id] = sig
        return sig

    def list_for_tenant(self, tenant_id: str, limit: int = 50) -> list[StoredSignal]:
        items = [s for s in self._signals.values() if s.tenant_id == tenant_id]
        items.sort(key=lambda s: s.created_at, reverse=True)
        return items[:limit]

    def get(self, signal_id: str) -> StoredSignal | None:
        return self._signals.get(signal_id)

class BacktestRepository:
    def __init__(self) -> None:
        self._reports: dict[str, BacktestReport] = {}

    def save_report(self, report: BacktestReport) -> None:
        self._reports[report.id] = report

    def list_for_tenant(self, tenant_id: str, limit: int = 50) -> list[BacktestReport]:
        items = [r for r in self._reports.values() if r.tenant_id == tenant_id]
        items.sort(key=lambda r: r.created_at, reverse=True)
        return items[:limit]


class JournalRepository:
    """Journal d'apprentissage en mémoire (entrées d'issue de signaux par agent)."""

    def __init__(self) -> None:
        self._entries: dict[str, list[dict]] = {}

    def add(self, tenant_id: str, entry: dict) -> None:
        self._entries.setdefault(tenant_id, []).append(entry)

    def list_for_tenant(self, tenant_id: str, limit: int = 200) -> list[dict]:
        return list(reversed(self._entries.get(tenant_id, [])))[:limit]

"""Repositories SQL (SQLAlchemy synchrone) — bascule production (use_in_memory_db=false).

Interface strictement identique aux repositories en mémoire : ils manipulent et retournent les
mêmes dataclasses (`User`, `Tenant`, `StoredSignal`), de sorte que l'API et les services restent
agnostiques du moteur de persistance.

Compatible Postgres (psycopg2) et SQLite (utilisé pour les tests de la couche SQL).
"""

from __future__ import annotations

import json
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.db import Base, SignalORM, TenantORM, UserORM
from app.models.entities import StoredSignal, Tenant, User


def make_engine_sessionmaker(url: str):
    """Crée un engine + sessionmaker et garantit l'existence des tables."""
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False, future=True)


# ---------- Mappings ORM <-> dataclasses ----------
def _user_to_entity(o: UserORM) -> User:
    return User(
        id=o.id,
        tenant_id=o.tenant_id,
        email=o.email,
        password_hash=o.password_hash,
        full_name=o.full_name,
        mfa_enabled=o.mfa_enabled,
        risk_profile=o.risk_profile,
        capital=o.capital,
        watchlist=json.loads(o.watchlist or "[]"),
        onboarded=o.onboarded,
    )


def _tenant_to_entity(o: TenantORM) -> Tenant:
    return Tenant(id=o.id, name=o.name, plan=o.plan)


class SqlUserRepository:
    def __init__(self, sm: sessionmaker[Session]) -> None:
        self._sm = sm

    def create(self, *, tenant_id: str, email: str, password_hash: str, full_name: str | None) -> User:
        email = email.lower()
        with self._sm() as s:
            if s.scalar(select(UserORM).where(UserORM.email == email)):
                raise ValueError("email déjà utilisé")
            o = UserORM(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                email=email,
                password_hash=password_hash,
                full_name=full_name,
                watchlist=json.dumps(["BTC/USDT"]),
            )
            s.add(o)
            s.commit()
            return _user_to_entity(o)

    def get(self, user_id: str) -> User | None:
        with self._sm() as s:
            o = s.get(UserORM, user_id)
            return _user_to_entity(o) if o else None

    def get_by_email(self, email: str) -> User | None:
        with self._sm() as s:
            o = s.scalar(select(UserORM).where(UserORM.email == email.lower()))
            return _user_to_entity(o) if o else None

    def update(self, user: User) -> User:
        with self._sm() as s:
            o = s.get(UserORM, user.id)
            if o is None:
                raise ValueError("utilisateur introuvable")
            o.risk_profile = user.risk_profile
            o.capital = user.capital
            o.watchlist = json.dumps(user.watchlist)
            o.onboarded = user.onboarded
            o.full_name = user.full_name
            o.mfa_enabled = user.mfa_enabled
            s.commit()
            return _user_to_entity(o)


class SqlTenantRepository:
    def __init__(self, sm: sessionmaker[Session]) -> None:
        self._sm = sm

    def create(self, name: str, plan: str = "free") -> Tenant:
        with self._sm() as s:
            o = TenantORM(id=str(uuid.uuid4()), name=name, plan=plan)
            s.add(o)
            s.commit()
            return _tenant_to_entity(o)

    def get(self, tenant_id: str) -> Tenant | None:
        with self._sm() as s:
            o = s.get(TenantORM, tenant_id)
            return _tenant_to_entity(o) if o else None

    def update(self, tenant: Tenant) -> Tenant:
        with self._sm() as s:
            o = s.get(TenantORM, tenant.id)
            if o is None:
                raise ValueError("tenant introuvable")
            o.plan = tenant.plan
            o.name = tenant.name
            s.commit()
            return _tenant_to_entity(o)


class SqlSignalRepository:
    def __init__(self, sm: sessionmaker[Session]) -> None:
        self._sm = sm

    def add(self, tenant_id: str, payload: dict) -> StoredSignal:
        with self._sm() as s:
            o = SignalORM(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                symbol=payload.get("asset", ""),
                direction=payload.get("direction", "HOLD"),
                entry=payload.get("entry", 0.0),
                stop_loss=payload.get("stop_loss", 0.0),
                take_profit_1=payload.get("take_profit_1"),
                take_profit_2=payload.get("take_profit_2"),
                take_profit_3=payload.get("take_profit_3"),
                risk_reward=payload.get("risk_reward"),
                confidence=payload.get("confidence", 0),
                timeframe=payload.get("timeframe"),
                rationale=payload.get("rationale"),
            )
            s.add(o)
            s.commit()
            return StoredSignal(id=o.id, tenant_id=tenant_id, payload=payload)

    def list_for_tenant(self, tenant_id: str, limit: int = 50) -> list[StoredSignal]:
        with self._sm() as s:
            rows = s.scalars(
                select(SignalORM)
                .where(SignalORM.tenant_id == tenant_id)
                .order_by(SignalORM.created_at.desc())
                .limit(limit)
            ).all()
            return [StoredSignal(id=r.id, tenant_id=tenant_id, payload=_signal_payload(r)) for r in rows]

    def get(self, signal_id: str) -> StoredSignal | None:
        with self._sm() as s:
            r = s.get(SignalORM, signal_id)
            return StoredSignal(id=r.id, tenant_id=r.tenant_id, payload=_signal_payload(r)) if r else None


def _signal_payload(r: SignalORM) -> dict:
    return {
        "asset": r.symbol,
        "direction": r.direction,
        "entry": r.entry,
        "stop_loss": r.stop_loss,
        "take_profit_1": r.take_profit_1,
        "take_profit_2": r.take_profit_2,
        "take_profit_3": r.take_profit_3,
        "risk_reward": r.risk_reward,
        "confidence": r.confidence,
        "timeframe": r.timeframe,
        "rationale": r.rationale,
    }

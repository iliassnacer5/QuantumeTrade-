"""Repositories SQL (SQLAlchemy synchrone) — bascule production (use_in_memory_db=false).

Interface strictement identique aux repositories en mémoire : ils manipulent et retournent les
mêmes dataclasses (`User`, `Tenant`, `StoredSignal`), de sorte que l'API et les services restent
agnostiques du moteur de persistance.

Compatible Postgres (psycopg2) et SQLite (utilisé pour les tests de la couche SQL).
"""

from __future__ import annotations

import json
import uuid

from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.db import Base, OhlcvORM, SignalORM, TenantORM, UserORM
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
        max_exposure_pct=o.max_exposure_pct,
        max_daily_signals=o.max_daily_signals,
        daily_loss_limit_pct=o.daily_loss_limit_pct,
        alert_email=o.alert_email,
        alert_telegram=o.alert_telegram,
        telegram_chat_id=o.telegram_chat_id,
        mfa_secret=o.mfa_secret,
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
            o.max_exposure_pct = user.max_exposure_pct
            o.max_daily_signals = user.max_daily_signals
            o.daily_loss_limit_pct = user.daily_loss_limit_pct
            o.alert_email = user.alert_email
            o.alert_telegram = user.alert_telegram
            o.telegram_chat_id = user.telegram_chat_id
            o.mfa_secret = user.mfa_secret
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
                position_value=payload.get("position_value"),
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


class SqlMarketRepository:
    """Persistance OHLCV (ingestion -> TimescaleDB en prod, table simple en test)."""

    def __init__(self, sm: sessionmaker[Session]) -> None:
        self._sm = sm

    def upsert_ohlcv(self, symbol: str, timeframe: str, rows: list[dict]) -> int:
        """Insère/MAJ des bougies (idempotent sur la clé symbol+timeframe+time). Retourne le nb traité."""
        count = 0
        with self._sm() as s:
            for r in rows:
                t = r["time"]
                ts = datetime.fromtimestamp(t, UTC) if isinstance(t, (int, float)) else t
                s.merge(
                    OhlcvORM(
                        symbol=symbol,
                        timeframe=timeframe,
                        time=ts,
                        open=r["open"],
                        high=r["high"],
                        low=r["low"],
                        close=r["close"],
                        volume=r.get("volume", 0.0),
                    )
                )
                count += 1
            s.commit()
        return count

    def count(self, symbol: str, timeframe: str) -> int:
        from sqlalchemy import func

        with self._sm() as s:
            return s.scalar(
                select(func.count())
                .select_from(OhlcvORM)
                .where(OhlcvORM.symbol == symbol, OhlcvORM.timeframe == timeframe)
            ) or 0


class NoopMarketRepository:
    """Pas de persistance OHLCV en mode in-memory (pas de TimescaleDB)."""

    def upsert_ohlcv(self, symbol: str, timeframe: str, rows: list[dict]) -> int:
        return 0

    def count(self, symbol: str, timeframe: str) -> int:
        return 0


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
        "position_value": r.position_value,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

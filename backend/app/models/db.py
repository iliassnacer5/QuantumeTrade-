"""Modèles SQLAlchemy (production, Postgres+TimescaleDB).

Définis pour la prod (use_in_memory_db=false). Le MVP/les tests utilisent les repositories
en mémoire. Le schéma SQL de référence reste `infra/db/init.sql`.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TenantORM(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    plan: Mapped[str] = mapped_column(String, default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserORM(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    risk_profile: Mapped[str] = mapped_column(String, default="moderate")
    capital: Mapped[float] = mapped_column(Float, default=10000.0)
    # Watchlist sérialisée en JSON (portable Postgres/SQLite).
    watchlist: Mapped[str] = mapped_column(Text, default="[]")
    onboarded: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SignalORM(Base):
    __tablename__ = "signals"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String, index=True)
    direction: Mapped[str] = mapped_column(String)
    entry: Mapped[float] = mapped_column(Float)
    stop_loss: Mapped[float] = mapped_column(Float)
    take_profit_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_2: Mapped[float | None] = mapped_column(Float, nullable=True)
    take_profit_3: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_reward: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer)
    timeframe: Mapped[str | None] = mapped_column(String, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

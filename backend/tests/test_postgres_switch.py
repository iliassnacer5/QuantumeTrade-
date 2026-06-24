"""Vérifie la bascule vers la persistance SQL (use_in_memory_db=false).

Utilise SQLite (même couche SQLAlchemy que Postgres) pour valider les repositories SQL et le
parcours API complet sans dépendre d'un serveur Postgres.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.repositories.sql import (
    SqlSignalRepository,
    SqlTenantRepository,
    SqlUserRepository,
    make_engine_sessionmaker,
)
from app.repositories.store import reset_store


def test_sql_repositories_lifecycle(tmp_path):
    url = f"sqlite:///{tmp_path / 'repo.db'}"
    _, sm = make_engine_sessionmaker(url)
    users = SqlUserRepository(sm)
    tenants = SqlTenantRepository(sm)
    signals = SqlSignalRepository(sm)

    tenant = tenants.create(name="acme")
    user = users.create(tenant_id=tenant.id, email="X@Test.com", password_hash="h", full_name="X")
    assert user.email == "x@test.com"  # normalisé en minuscules
    assert users.get(user.id).id == user.id
    assert users.get_by_email("x@test.com").id == user.id

    # update persistant
    user.onboarded = True
    user.capital = 5000
    user.watchlist = ["BTC/USDT", "ETH/USDT"]
    users.update(user)
    reloaded = users.get(user.id)
    assert reloaded.onboarded is True
    assert reloaded.capital == 5000
    assert reloaded.watchlist == ["BTC/USDT", "ETH/USDT"]

    # plan tenant
    tenant.plan = "starter"
    tenants.update(tenant)
    assert tenants.get(tenant.id).plan == "starter"

    # signaux + isolation
    signals.add(tenant.id, {"asset": "BTC/USDT", "direction": "BUY", "entry": 1, "stop_loss": 0.9, "confidence": 70})
    assert len(signals.list_for_tenant(tenant.id)) == 1
    assert signals.list_for_tenant("autre-tenant") == []


@pytest.fixture
def sql_backend(tmp_path):
    """Force l'app à utiliser le backend SQL (SQLite) le temps du test."""
    settings = get_settings()
    old_mem, old_url = settings.use_in_memory_db, settings.database_url
    settings.use_in_memory_db = False
    settings.database_url = f"sqlite:///{tmp_path / 'api.db'}"
    reset_store()
    try:
        yield
    finally:
        settings.use_in_memory_db, settings.database_url = old_mem, old_url
        reset_store()


def test_full_api_flow_on_sql(sql_backend, monkeypatch):
    async def fake_fetch(*a, **k):
        raise RuntimeError("offline")

    monkeypatch.setattr("app.data.binance.fetch_klines", fake_fetch)

    client = TestClient(app)
    r = client.post("/api/auth/register", json={"email": "sql@test.com", "password": "password123"})
    assert r.status_code == 201
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}

    assert client.post(
        "/api/onboarding",
        json={"risk_profile": "aggressive", "capital": 20000, "watchlist": ["BTC/USDT"]},
        headers=h,
    ).json()["onboarded"] is True

    assert client.post("/api/signals/generate", json={"asset": "BTC/USDT"}, headers=h).status_code == 200
    listed = client.get("/api/signals", headers=h).json()
    assert len(listed) == 1
    # Vérifie que les données ont bien transité par la base (rationale persistée).
    assert listed[0]["rationale"]
    assert client.get("/api/auth/me", headers=h).json()["capital"] == 20000

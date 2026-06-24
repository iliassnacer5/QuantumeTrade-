"""Tests des lots de complétion Phase 1 : risque, settings/alertes, P&L, heatmap, MFA, audit, rate limit."""

import pytest
from fastapi.testclient import TestClient

from app.core import totp
from app.core.config import get_settings
from app.main import app


@pytest.fixture
def offline(monkeypatch):
    async def fake_klines(*a, **k):
        raise RuntimeError("offline")

    async def fake_24h(*a, **k):
        raise RuntimeError("offline")

    monkeypatch.setattr("app.data.binance.fetch_klines", fake_klines)
    monkeypatch.setattr("app.data.ohlcv._binance_ohlcv", fake_24h)
    monkeypatch.setattr("app.data.heatmap._binance_24h", fake_24h)
    yield


def _auth(client, email="u@test.com"):
    r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------- Lot 2 : risque ----------
def test_risk_status_and_limit(offline):
    client = TestClient(app)
    h = _auth(client, "risk@test.com")
    client.post("/api/onboarding", json={"risk_profile": "moderate", "capital": 10000, "watchlist": ["BTC/USDT"]}, headers=h)
    # Limiter à 1 signal/jour
    client.patch("/api/settings", json={"max_daily_signals": 1}, headers=h)
    assert client.post("/api/signals/generate", json={"asset": "BTC/USDT"}, headers=h).status_code == 200
    # 2e génération bloquée par le garde-fou
    assert client.post("/api/signals/generate", json={"asset": "BTC/USDT"}, headers=h).status_code == 429
    st = client.get("/api/risk/status", headers=h).json()
    assert st["daily_signals"] >= 1
    assert st["max_daily_signals"] == 1


# ---------- Lot 3 : settings / alertes / P&L / heatmap ----------
def test_settings_update(offline):
    client = TestClient(app)
    h = _auth(client, "set@test.com")
    r = client.patch(
        "/api/settings",
        json={"alert_telegram": True, "telegram_chat_id": "12345", "max_exposure_pct": 30},
        headers=h,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["alert_telegram"] is True
    assert body["telegram_chat_id"] == "12345"
    assert body["max_exposure_pct"] == 30


def test_portfolio_pnl(offline):
    client = TestClient(app)
    h = _auth(client, "pnl@test.com")
    client.post("/api/onboarding", json={"risk_profile": "aggressive", "capital": 10000, "watchlist": ["BTC/USDT"]}, headers=h)
    client.post("/api/signals/generate", json={"asset": "BTC/USDT"}, headers=h)
    r = client.get("/api/portfolio", headers=h)
    assert r.status_code == 200
    assert "total_pnl" in r.json() and "positions" in r.json()


def test_heatmap(offline):
    client = TestClient(app)
    h = _auth(client, "heat@test.com")
    client.post("/api/onboarding", json={"risk_profile": "moderate", "capital": 5000, "watchlist": ["BTC/USDT", "ETH/USDT"]}, headers=h)
    r = client.get("/api/market/heatmap", headers=h)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    assert {"symbol", "price", "change_pct"} <= set(rows[0])


# ---------- Lot 5 : MFA ----------
def test_mfa_flow(offline):
    client = TestClient(app)
    h = _auth(client, "mfa@test.com")
    setup = client.post("/api/auth/mfa/setup", headers=h).json()
    secret = setup["secret"]
    assert setup["otpauth_uri"].startswith("otpauth://")
    # Activation avec un code valide
    code = totp.totp_now(secret)
    assert client.post("/api/auth/mfa/enable", json={"code": code}, headers=h).status_code == 200
    # Login sans code -> 401
    assert client.post("/api/auth/login", json={"email": "mfa@test.com", "password": "password123"}).status_code == 401
    # Login avec code -> 200
    ok = client.post(
        "/api/auth/login",
        json={"email": "mfa@test.com", "password": "password123", "mfa_code": totp.totp_now(secret)},
    )
    assert ok.status_code == 200


# ---------- Lot 5 : audit ----------
def test_audit_log(offline):
    client = TestClient(app)
    h = _auth(client, "audit@test.com")
    r = client.get("/api/audit", headers=h)
    assert r.status_code == 200
    actions = [e["action"] for e in r.json()]
    assert "user.register" in actions


# ---------- Lot 5 : rate limiting (réactivé localement) ----------
def test_rate_limit_blocks(monkeypatch):
    get_settings().rate_limit_enabled = True
    try:
        client = TestClient(app)
        codes = [
            client.post("/api/auth/login", json={"email": "x@test.com", "password": "bad"}).status_code
            for _ in range(15)
        ]
        assert 429 in codes  # la limite login (10/min) doit déclencher
    finally:
        get_settings().rate_limit_enabled = False

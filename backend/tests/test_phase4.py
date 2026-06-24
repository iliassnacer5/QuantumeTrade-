"""Tests Phase 4 : exécution broker (paper + garde-fous KYC), copy-trading, marketplace."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core import crypto
from app.main import app
from app.repositories.store import get_store
from app.services import copytrading_service as copy
from app.services import execution_service as execu


def _register(client: TestClient) -> tuple[dict, str]:
    email = f"u{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    return h, r.json()["access_token"]


def _upgrade(client: TestClient, h: dict, plan: str) -> None:
    assert client.post(f"/api/billing/checkout/{plan}", headers=h).status_code == 200


# ---------------- Crypto ----------------
def test_crypto_roundtrip_and_tamper():
    tok = crypto.encrypt("super-secret-broker-key")
    assert crypto.decrypt(tok) == "super-secret-broker-key"
    with pytest.raises(ValueError):
        crypto.decrypt(tok[:-3] + "AAA")
    assert crypto.mask("ABCDEFGH").endswith("EFGH")


# ---------------- Generic record store ----------------
def test_record_store_crud():
    store = get_store()
    store.records.put("ut_kind", "id1", {"x": 1}, tenant_id="t1")
    store.records.put("ut_kind", "id2", {"x": 2}, tenant_id="t2")
    assert store.records.get("ut_kind", "id1")["x"] == 1
    assert len(store.records.list("ut_kind")) >= 2
    assert len(store.records.list("ut_kind", tenant_id="t1")) == 1
    assert store.records.delete("ut_kind", "id1") is True


# ---------------- Exécution broker ----------------
def test_execution_gated_elite():
    client = TestClient(app)
    h, _ = _register(client)
    _upgrade(client, h, "pro")  # pro != elite -> auto_execution refusé
    assert client.get("/api/execution/brokers", headers=h).status_code == 402


def test_paper_order_flow():
    client = TestClient(app)
    h, _ = _register(client)
    _upgrade(client, h, "elite")
    # Connexion broker papier
    conn = client.post("/api/execution/brokers", json={"broker": "paper", "mode": "paper"}, headers=h)
    assert conn.status_code == 201
    cid = conn.json()["id"]
    assert "key_hint" in conn.json()
    # Passe un ordre papier -> filled
    order = client.post(
        "/api/execution/orders",
        json={"conn_id": cid, "symbol": "BTC/USDT", "side": "buy", "qty": 0.01},
        headers=h,
    )
    assert order.status_code == 201
    body = order.json()
    assert body["status"] == "filled" and body["mode"] == "paper" and body["filled_price"] is not None
    assert len(client.get("/api/execution/orders", headers=h).json()) >= 1


def test_live_requires_kyc():
    client = TestClient(app)
    h, _ = _register(client)
    _upgrade(client, h, "elite")
    # Sans KYC : connexion live refusée
    r = client.post(
        "/api/execution/brokers",
        json={"broker": "alpaca", "api_key": "k", "api_secret": "s", "mode": "live"},
        headers=h,
    )
    assert r.status_code == 400 and "KYC" in r.json()["detail"]
    # Soumet KYC -> vérifié (démo)
    assert client.post("/api/kyc", json={"legal_name": "Jean Test", "country": "FR", "doc_id": "X123"}, headers=h).json()["status"] == "verified"
    # Désormais la connexion live est acceptée (clé chiffrée, jamais renvoyée)
    r2 = client.post(
        "/api/execution/brokers",
        json={"broker": "alpaca", "api_key": "AKID", "api_secret": "SEC", "mode": "live"},
        headers=h,
    )
    assert r2.status_code == 201 and r2.json()["mode"] == "live"
    assert "api_key" not in r2.json() and "api_secret" not in r2.json()


def test_broker_key_stored_encrypted():
    store = get_store()
    conn = execu.connect_broker(store, "tnt-enc", broker="paper", api_key="PLAINKEY", api_secret="PLAINSEC", mode="paper")
    raw = store.records.get(execu.CONN, conn["id"])
    assert raw["api_key_enc"] != "PLAINKEY" and "PLAINKEY" not in raw["api_key_enc"]
    assert crypto.decrypt(raw["api_key_enc"]) == "PLAINKEY"


# ---------------- Copy-trading ----------------
def test_copytrading_gated_elite():
    client = TestClient(app)
    h, _ = _register(client)
    _upgrade(client, h, "pro")
    assert client.get("/api/copytrading/leaderboard", headers=h).status_code == 402


@pytest.mark.asyncio
async def test_copy_fanout_with_risk_and_commission():
    store = get_store()
    leader = "leader-tnt"
    follower = "follower-tnt"
    # Le leader publie son profil (opt-in)
    copy.publish_profile(store, leader, "Pro Trader")
    assert any(p["tenant_id"] == leader for p in copy.leaderboard(store))
    # Le follower suit avec contrôle de risque
    f = copy.follow(store, follower, leader, allocation_pct=10, max_per_trade=500, min_confidence=50)
    assert f["leader_tenant"] == leader
    # Un signal du leader est répliqué
    class Card:
        asset = "BTC/USDT"
        direction = type("D", (), {"value": "BUY"})()
        entry = 100.0
        confidence = 70
    n = await copy.on_leader_signal(store, leader, Card())
    assert n == 1
    # Commission créditée au leader + ordre copié chez le follower
    assert copy.commissions(store, leader)["count"] >= 1
    follower_orders = store.records.list("order", follower)
    assert any(o.get("copied_from") == leader for o in follower_orders)


@pytest.mark.asyncio
async def test_copy_skips_below_confidence():
    store = get_store()
    leader, follower = "lead2", "foll2"
    copy.publish_profile(store, leader, "T")
    copy.follow(store, follower, leader, min_confidence=80)
    class Card:
        asset = "BTC/USDT"
        direction = type("D", (), {"value": "BUY"})()
        entry = 100.0
        confidence = 60  # sous le seuil
    assert await copy.on_leader_signal(store, leader, Card()) == 0


def test_cannot_follow_self():
    client = TestClient(app)
    h, _ = _register(client)
    _upgrade(client, h, "elite")
    me = client.get("/api/auth/me", headers=h).json()
    client.post("/api/copytrading/publish", json={"display_name": "Me"}, headers=h)
    # suivre son propre tenant => 400
    # (tenant_id non exposé côté client : on teste via le service)
    from app.repositories.store import get_store as gs
    store = gs()
    import pytest as _pytest
    with _pytest.raises(ValueError):
        copy.follow(store, store.users.get_by_email(me["email"]).tenant_id, store.users.get_by_email(me["email"]).tenant_id)


# ---------------- Marketplace ----------------
def test_marketplace_listing_and_purchase():
    client = TestClient(app)
    seller_h, _ = _register(client)
    _upgrade(client, seller_h, "pro")  # marketplace_sell = pro
    listing = client.post(
        "/api/marketplace/listings",
        json={"title": "Momentum Pro", "kind": "strategy", "price": 49, "description": "EMA cross", "config": {"weights": {"technical": 0.5}}},
        headers=seller_h,
    )
    assert listing.status_code == 201
    lid = listing.json()["id"]
    # config non révélée à la navigation
    browse = client.get("/api/marketplace/listings", headers=seller_h).json()
    assert all("config" not in l for l in browse)
    # Un autre user achète -> config débloquée
    buyer_h, _ = _register(client)
    buy = client.post(f"/api/marketplace/listings/{lid}/buy", headers=buyer_h)
    assert buy.status_code == 200 and "weights" in buy.json()["config"]
    assert len(client.get("/api/marketplace/purchases", headers=buyer_h).json()) == 1


def test_dev_api_keys_elite():
    client = TestClient(app)
    h, _ = _register(client)
    # free -> 402
    assert client.get("/api/marketplace/api-keys", headers=h).status_code == 402
    _upgrade(client, h, "elite")
    key = client.post("/api/marketplace/api-keys", json={"label": "prod"}, headers=h)
    assert key.status_code == 201
    raw = key.json()["api_key"]
    assert raw.startswith("qta_")
    keys = client.get("/api/marketplace/api-keys", headers=h).json()
    # la clé en clair n'est jamais re-listée (seulement le prefix)
    assert all("api_key" not in k for k in keys) and keys[0]["prefix"] == raw[:12]

"""Tests Phase 5 : observabilité (/metrics, health), cache LLM, i18n, white-label, multi-comptes."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core import i18n, metrics
from app.core.config import get_settings
from app.main import app


def _register(client: TestClient):
    email = f"u{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _upgrade(client, h, plan):
    assert client.post(f"/api/billing/checkout/{plan}", headers=h).status_code == 200


# ---------------- Observabilité ----------------
def test_metrics_endpoint_prometheus_format():
    client = TestClient(app)
    client.get("/health")  # génère du trafic
    r = client.get("/metrics")
    assert r.status_code == 200
    body = r.text
    assert "# TYPE http_requests_total counter" in body
    assert "http_requests_total{" in body
    assert "http_request_duration_seconds_bucket{" in body


def test_request_id_header():
    client = TestClient(app)
    r = client.get("/health")
    assert r.headers.get("X-Request-ID")


def test_health_ready_and_live():
    client = TestClient(app)
    live = client.get("/health/live").json()
    assert live["status"] == "alive" and "uptime_seconds" in live
    ready = client.get("/health/ready").json()
    assert ready["status"] in ("ready", "degraded") and "database" in ready["checks"]


def test_metrics_counter_helpers():
    metrics.reset()
    metrics.inc("ut_counter_total", 2, kind="a")
    metrics.observe("ut_latency_seconds", 0.3)
    out = metrics.render()
    assert 'ut_counter_total{kind="a"} 2' in out
    assert "ut_latency_seconds_count" in out


# ---------------- Cache LLM ----------------
@pytest.mark.asyncio
async def test_llm_cache_hit(monkeypatch):
    from app.agents import llm

    metrics.reset()
    s = get_settings()
    s.google_api_key = "k"
    s.llm_enabled = True
    calls = {"n": 0}

    async def fake(model, messages, api_key, max_tokens):
        calls["n"] += 1
        return "réponse"

    monkeypatch.setattr("app.agents.llm._acompletion", fake)
    try:
        a = await llm.complete("même prompt", role="fast")
        b = await llm.complete("même prompt", role="fast")
        assert a == b == "réponse"
        assert calls["n"] == 1  # 2e appel servi par le cache
        assert 'llm_cache_hits_total{role="fast"} 1' in metrics.render()
    finally:
        s.google_api_key = ""


# ---------------- i18n ----------------
def test_i18n_resolution():
    assert i18n.normalize("en-US,en;q=0.9") == "en"
    assert i18n.normalize("de") == "fr"  # repli défaut
    assert i18n.t("nav.signals", "en") == "Signals"
    assert i18n.t("nav.signals", "fr") == "Signaux"


def test_i18n_endpoint_and_locale_setting():
    client = TestClient(app)
    en = client.get("/api/i18n/en").json()
    assert en["locale"] == "en" and en["messages"]["nav.copilot"] == "AI Copilot"
    # locale via Accept-Language
    neg = client.get("/api/i18n", headers={"Accept-Language": "en"}).json()
    assert neg["locale"] == "en"
    # préférence persistée
    h = _register(client)
    assert client.patch("/api/settings", json={"locale": "en"}, headers=h).json()["locale"] == "en"


# ---------------- White-label ----------------
def test_white_label_gated_and_resolution():
    client = TestClient(app)
    h = _register(client)
    # branding par défaut lisible
    assert client.get("/api/branding", headers=h).json()["brand_name"] == "Quantum Trade AI"
    # modification réservée Enterprise -> 402 sans le plan
    assert client.put("/api/branding", json={"brand_name": "ACME"}, headers=h).status_code == 402
    _upgrade(client, h, "enterprise")
    r = client.put(
        "/api/branding",
        json={"brand_name": "ACME Bank", "primary_color": "#0055FF", "custom_domain": "trade.acme.com"},
        headers=h,
    )
    assert r.status_code == 200 and r.json()["brand_name"] == "ACME Bank"
    # résolution publique par domaine
    pub = client.get("/api/branding/resolve", params={"domain": "trade.acme.com"}).json()
    assert pub["brand_name"] == "ACME Bank" and pub["primary_color"] == "#0055FF"


def test_enterprise_plan_listed():
    client = TestClient(app)
    plans = client.get("/api/billing/plans").json()
    assert any(p["id"] == "enterprise" for p in plans)


# ---------------- Multi-comptes avancé ----------------
def test_seat_limit_enforced(monkeypatch):
    from app.api import team

    client = TestClient(app)
    h = _register(client)
    _upgrade(client, h, "pro")
    monkeypatch.setitem(team.SEAT_LIMITS, "pro", 2)  # owner + 1 invité max
    r1 = client.post("/api/team/invite", json={"email": f"a{uuid.uuid4().hex[:6]}@t.com"}, headers=h)
    assert r1.status_code == 201
    r2 = client.post("/api/team/invite", json={"email": f"b{uuid.uuid4().hex[:6]}@t.com"}, headers=h)
    assert r2.status_code == 402  # limite de sièges atteinte

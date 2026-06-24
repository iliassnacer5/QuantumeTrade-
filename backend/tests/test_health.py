"""Test du endpoint /health (Definition of Done Phase 0)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "quantum-trade-ai-backend"


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Quantum Trade AI API" in resp.json()["message"]

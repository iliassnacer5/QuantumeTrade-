"""Tests du routeur d'intention du Copilot (Phase 3 — copilot complet).

Couvre : détection d'intention par mots-clés, extraction de symbole, et le repli déterministe
de chaque intention via l'endpoint /api/copilot/ask (sans clé LLM -> chemin déterministe).
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services import copilot_service as cs


# ---------------- Unitaires : extraction de symbole ----------------
@pytest.mark.parametrize(
    "message, default, expected",
    [
        ("dois-je trader btc ?", None, "BTC/USDT"),
        ("je regarde ETH/USDT", None, "ETH/USDT"),
        ("faut-il acheter EURUSD maintenant", None, "EUR/USD"),
        ("AAPL est-elle un bon trade ?", None, "AAPL"),
        ("comment sont les marchés ?", None, None),
        ("rien de connu ici xyzzy", "SOL/USDT", "SOL/USDT"),
    ],
)
def test_extract_symbol(message, default, expected):
    assert cs._extract_symbol(message, default) == expected


# ---------------- Unitaires : détection d'intention ----------------
@pytest.mark.parametrize(
    "message, symbol, expected",
    [
        ("Quels trades je dois faire aujourd'hui ?", None, "todays_trades"),
        ("Comment sont les marchés ce matin ?", None, "market_overview"),
        ("Dois-je trader BTC ?", "BTC/USDT", "should_i_trade"),
        ("Les meilleures paires crypto ?", None, "scan"),
        ("Analyse ETH/USDT", "ETH/USDT", "analyze"),
        ("Bonjour", None, "general"),
    ],
)
def test_detect_intent(message, symbol, expected):
    assert cs.detect_intent(message, symbol) == expected


def test_detect_class():
    assert cs._detect_class("meilleures paires forex") == "forex"
    assert cs._detect_class("top crypto du jour") == "crypto"
    assert cs._detect_class("scanne les actions us") == "stock"
    assert cs._detect_class("scanne le marché") is None


# ---------------- API : repli déterministe par intention ----------------
def _pro_client(monkeypatch) -> tuple[TestClient, dict]:
    s = get_settings()
    s.anthropic_api_key = ""
    s.google_api_key = ""
    client = TestClient(app)
    email = f"u{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/auth/register", json={"email": email, "password": "password123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.post("/api/billing/checkout/pro", headers=h).status_code == 200
    return client, h


def _ask(client: TestClient, h: dict, message: str) -> str:
    r = client.post("/api/copilot/ask", json={"message": message}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()["answer"]


def test_fallback_todays_trades(monkeypatch):
    client, h = _pro_client(monkeypatch)
    answer = _ask(client, h, "Quels trades je dois faire aujourd'hui ?")
    assert len(answer) > 0
    assert "jour" in answer.lower() or "abstenir" in answer.lower()


def test_fallback_market_overview(monkeypatch):
    client, h = _pro_client(monkeypatch)
    answer = _ask(client, h, "Comment sont les marchés aujourd'hui ?")
    assert "marché" in answer.lower() or "sessions" in answer.lower() or "régime" in answer.lower()


def test_fallback_should_i_trade(monkeypatch):
    client, h = _pro_client(monkeypatch)
    answer = _ask(client, h, "Dois-je trader BTC ?")
    assert "BTC/USDT" in answer
    # Verdict OUI/NON/POSSIBLE présent.
    assert any(tok in answer for tok in ("OUI", "NON", "POSSIBLE", "pas de trade"))

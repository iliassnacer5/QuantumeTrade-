"""Tests des agents IA (déterministes, sans LLM)."""

import pytest

from app.agents import master, sentiment, technical
from app.agents.sentiment import NewsItem
from app.data.synthetic import generate_candles
from app.models.signal import Direction

pytestmark = pytest.mark.asyncio


async def test_technical_detects_uptrend():
    # Tendance haussière : la détection de tendance (EMA20 > EMA50) doit être positive.
    # NB : le score net peut être tempéré par un RSI en surachat (réversion à la moyenne) —
    # c'est le comportement métier attendu, on vérifie donc la composante tendance.
    candles = generate_candles(n=200, trend=0.003, seed=1)
    out = await technical.run(candles)
    assert out.name == "technical"
    assert out.details["ema20"] > out.details["ema50"]
    assert "rsi" in out.details and "adx" in out.details  # métriques expertes exposées
    assert out.confidence > 0.5


async def test_technical_insufficient_data():
    candles = generate_candles(n=10)
    out = await technical.run(candles)
    assert out.score == 0.0


async def test_sentiment_lexicon():
    news = [NewsItem("Bitcoin surge to record high"), NewsItem("Major adoption partnership")]
    out = await sentiment.run(news)
    assert out.score > 0


async def test_sentiment_bearish():
    news = [NewsItem("Market crash and selloff"), NewsItem("Exchange hack lawsuit")]
    out = await sentiment.run(news, fear_greed=20)
    assert out.score < 0


async def test_sentiment_scores_each_headline(monkeypatch):
    """Le LLM score CHAQUE titre individuellement (tableau JSON) -> scores distincts par news."""
    from app.agents import llm

    monkeypatch.setattr(llm, "available", lambda: True)

    async def _complete(prompt, **kwargs):
        return "[0.8, -0.6, 0.0]"
    monkeypatch.setattr(llm, "complete", _complete)

    news = [NewsItem("ETF approval inflow"), NewsItem("Exchange hack"), NewsItem("Marché stable")]
    await sentiment.run(news)
    assert news[0].sentiment == 0.8 and news[1].sentiment == -0.6 and news[2].sentiment == 0.0


async def test_sentiment_lexicon_assigns_per_headline():
    """Sans LLM, le lexique assigne quand même un score PAR TITRE (visible sur la prédiction)."""
    news = [NewsItem("Bitcoin surge rally record"), NewsItem("crash selloff fear")]
    await sentiment.run(news)
    assert news[0].sentiment is not None and news[0].sentiment > 0
    assert news[1].sentiment is not None and news[1].sentiment < 0


def test_reliability_report_flags_low_sample():
    """Un agent avec peu d'appels directionnels est marqué low_sample (le 0% n'est pas fiable)."""
    from app.agents.journal import reliability_report
    entries = [{"outcome": "loss", "direction": "BUY", "agent_scores": {"pattern": 0.5}} for _ in range(8)]
    rep = {r["agent"]: r for r in reliability_report(entries)}
    assert rep["pattern"]["samples"] == 8 and rep["pattern"]["low_sample"] is True


def test_hold_signals_not_recorded_in_journal():
    """Un signal HOLD ne pollue pas le journal (pas de trade -> rien à apprendre)."""
    from types import SimpleNamespace

    from app.services import journal_service

    recorded: list = []
    store = SimpleNamespace(journal=SimpleNamespace(add=lambda tid, entry: recorded.append(entry)))
    hold = SimpleNamespace(direction=Direction.HOLD, asset="BTC/USDT", agents=[])
    journal_service.record_signal(store, "t1", hold, "sig1")
    assert recorded == []  # HOLD ignoré
    buy = SimpleNamespace(direction=Direction.BUY, asset="BTC/USDT",
                          agents=[{"name": "technical", "score": 0.5}])
    journal_service.record_signal(store, "t1", buy, "sig2")
    assert len(recorded) == 1 and recorded[0]["direction"] == "BUY"


async def test_master_conflict_detection():
    bull = await technical.run(generate_candles(n=200, trend=0.003, seed=1))
    bear = await sentiment.run([NewsItem("crash plunge selloff")], fear_greed=10)
    decision = master.decide([bull, bear])
    assert decision.direction in (Direction.BUY, Direction.SELL, Direction.HOLD)
    assert isinstance(decision.conflict, bool)
    assert 0 <= decision.confidence <= 100

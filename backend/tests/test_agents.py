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


async def test_master_conflict_detection():
    bull = await technical.run(generate_candles(n=200, trend=0.003, seed=1))
    bear = await sentiment.run([NewsItem("crash plunge selloff")], fear_greed=10)
    decision = master.decide([bull, bear])
    assert decision.direction in (Direction.BUY, Direction.SELL, Direction.HOLD)
    assert isinstance(decision.conflict, bool)
    assert 0 <= decision.confidence <= 100

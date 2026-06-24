"""Tests des indicateurs techniques déterministes."""

from app.domain import indicators as ind
from app.domain.indicators import Candle


def test_ema_length_and_trend():
    vals = [float(i) for i in range(1, 51)]
    e = ind.ema(vals, 10)
    assert len(e) == len(vals)
    assert e[-1] < vals[-1]  # EMA en retard sur une série croissante


def test_rsi_strong_uptrend_high():
    closes = [float(i) for i in range(1, 60)]  # hausse monotone
    r = ind.rsi(closes, 14)
    assert r is not None and r > 70


def test_rsi_downtrend_low():
    closes = [float(i) for i in range(60, 1, -1)]
    r = ind.rsi(closes, 14)
    assert r is not None and r < 30


def test_rsi_insufficient_data():
    assert ind.rsi([1, 2, 3], 14) is None


def test_macd_returns_triplet():
    closes = [float(i % 10) + i * 0.1 for i in range(60)]
    res = ind.macd(closes)
    assert res is not None and len(res) == 3


def test_bollinger_ordering():
    closes = [100 + (i % 5) for i in range(30)]
    boll = ind.bollinger(closes, 20)
    assert boll is not None
    low, mid, high = boll
    assert low <= mid <= high


def test_atr_positive():
    candles = [Candle(10, 11, 9, 10.5, 100) for _ in range(30)]
    a = ind.atr(candles, 14)
    assert a is not None and a > 0

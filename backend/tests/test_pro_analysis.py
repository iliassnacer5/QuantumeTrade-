"""Tests de l'analyse pro : pivots, Fibonacci, figures chandeliers avancées, volume climax."""

from __future__ import annotations

from app.agents.pattern import detect_patterns
from app.domain import indicators as ind
from app.domain.indicators import Candle


def _c(o, h, l, c, v=100.0):  # noqa: E741
    return Candle(o, h, l, c, v)


def _flat(n=60, price=100.0, vol=100.0):
    return [_c(price, price + 1, price - 1, price, vol) for _ in range(n)]


# ---------------- Indicateurs pro ----------------
def test_pivot_points():
    candles = _flat(30)
    piv = ind.pivot_points(candles)
    assert piv and piv["s2"] < piv["s1"] < piv["p"] < piv["r1"] < piv["r2"]


def test_fibonacci_levels_uptrend():
    # bas au début, haut à la fin -> swing haussier, retracements sous le haut
    candles = [_c(100 + i, 101 + i, 99 + i, 100 + i) for i in range(80)]
    fib = ind.fibonacci_levels(candles)
    assert fib and fib["swing"] == "haussier"
    lv = fib["levels"]
    assert lv["61.8"] < lv["50"] < lv["38.2"] < fib["high"]


# ---------------- Figures chandeliers pro ----------------
def _base(n=30):
    return [_c(100, 101, 99, 100) for _ in range(n)]


def test_morning_star():
    candles = _base() + [_c(100, 100.5, 96, 96.5), _c(96.4, 96.9, 96.0, 96.5), _c(96.6, 99.5, 96.5, 99.2)]
    names = [p for p, _ in detect_patterns(candles)]
    assert "étoile du matin" in names


def test_evening_star():
    candles = _base() + [_c(100, 104, 99.9, 103.8), _c(103.9, 104.3, 103.5, 103.8), _c(103.7, 103.8, 100.2, 100.5)]
    names = [p for p, _ in detect_patterns(candles)]
    assert "étoile du soir" in names


def test_three_white_soldiers():
    candles = _base() + [_c(100, 102, 99.8, 101.8), _c(101.8, 103.8, 101.6, 103.6), _c(103.6, 105.6, 103.4, 105.4)]
    names = [p for p, _ in detect_patterns(candles)]
    assert "trois soldats blancs" in names


def test_dark_cloud_cover():
    candles = _base() + [_c(100, 103, 99.9, 102.8), _c(103.2, 103.5, 100.9, 101.1)]
    names = [p for p, _ in detect_patterns(candles)]
    assert "dark cloud cover (retournement baissier)" in names


def test_inside_bar():
    candles = _base() + [_c(100, 105, 95, 102), _c(101, 103, 99, 100)]
    names = [p for p, _ in detect_patterns(candles)]
    assert "inside bar (compression)" in names


def test_double_top():
    # deux sommets ~104 séparés, prix qui rejette sous le haut
    mid = [_c(100, 101, 99, 100) for _ in range(8)]
    candles = (_base(20) + [_c(100, 104, 99, 103)] + mid + [_c(100, 104.05, 99, 103)]
               + [_c(102, 102.5, 100, 100.5) for _ in range(6)])
    names = [p for p, _ in detect_patterns(candles)]
    assert "double sommet (résistance confirmée)" in names


# ---------------- Volume pro ----------------
async def test_volume_climax():
    from app.agents import volume as vol_agent
    candles = _flat(25, vol=100.0)
    candles[-1] = _c(100, 103, 99.8, 102.8, v=350.0)  # pic 3.5× sur bougie haussière
    out = await vol_agent.run(candles)
    assert "Pic de volume" in out.rationale
    assert out.score > 0  # mouvement haussier confirmé par le volume


async def test_technical_metrics_include_pro_levels():
    from app.domain import ta
    candles = [_c(100 + i * 0.2, 101 + i * 0.2, 99 + i * 0.2, 100 + i * 0.2) for i in range(120)]
    a = ta.analyze(candles)
    assert "pivots" in a["metrics"] and "fibonacci" in a["metrics"] and "pos_52" in a["metrics"]

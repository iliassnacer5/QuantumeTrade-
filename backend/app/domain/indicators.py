"""Indicateurs techniques déterministes (pur Python, sans dépendance native).

Implémente RSI, EMA, MACD, Bandes de Bollinger, ATR.
Utilisés par l'Agent Technique (M2) — calculs reproductibles, pas de LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Candle:
    """Bougie OHLCV. `timestamp` optionnel (renseigné pour le backtest, None en live/synthétique)."""

    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime | None = None


def ema(values: list[float], period: int) -> list[float]:
    """Moyenne mobile exponentielle. Retourne une liste de même longueur (None implicite=premières valeurs lissées)."""
    if not values:
        return []
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def sma(values: list[float], period: int) -> float | None:
    """Moyenne mobile simple sur les `period` dernières valeurs."""
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def rsi(closes: list[float], period: int = 14) -> float | None:
    """Relative Strength Index (0-100). Méthode de Wilder."""
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(max(-delta, 0.0))
    # Moyenne de Wilder
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(
    closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[float, float, float] | None:
    """MACD -> (ligne MACD, ligne signal, histogramme). Renvoie None si pas assez de données."""
    if len(closes) < slow + signal:
        return None
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal)
    hist = macd_line[-1] - signal_line[-1]
    return macd_line[-1], signal_line[-1], hist


def bollinger(closes: list[float], period: int = 20, mult: float = 2.0) -> tuple[float, float, float] | None:
    """Bandes de Bollinger -> (bande basse, milieu, bande haute)."""
    if len(closes) < period:
        return None
    window = closes[-period:]
    mid = sum(window) / period
    variance = sum((c - mid) ** 2 for c in window) / period
    std = variance**0.5
    return mid - mult * std, mid, mid + mult * std


def atr(candles: list[Candle], period: int = 14) -> float | None:
    """Average True Range — mesure de volatilité (base du dimensionnement SL/TP)."""
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        c = candles[i]
        prev_close = candles[i - 1].close
        tr = max(c.high - c.low, abs(c.high - prev_close), abs(c.low - prev_close))
        trs.append(tr)
    # ATR de Wilder
    atr_val = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr_val = (atr_val * (period - 1) + trs[i]) / period
    return atr_val


def stochastic(candles: list[Candle], period: int = 14, smooth: int = 3) -> tuple[float, float] | None:
    """Oscillateur stochastique -> (%K, %D). 0-100. >80 surachat, <20 survente."""
    if len(candles) < period + smooth:
        return None
    ks: list[float] = []
    for i in range(period - 1, len(candles)):
        window = candles[i - period + 1 : i + 1]
        hh = max(c.high for c in window)
        ll = min(c.low for c in window)
        k = 100.0 if hh == ll else (candles[i].close - ll) / (hh - ll) * 100.0
        ks.append(k)
    if len(ks) < smooth:
        return None
    d = sum(ks[-smooth:]) / smooth
    return ks[-1], d


def adx(candles: list[Candle], period: int = 14) -> float | None:
    """Average Directional Index — force de la tendance (0-100). >25 = tendance, <20 = range."""
    if len(candles) < 2 * period:
        return None
    trs: list[float] = []
    plus_dm: list[float] = []
    minus_dm: list[float] = []
    for i in range(1, len(candles)):
        up = candles[i].high - candles[i - 1].high
        down = candles[i - 1].low - candles[i].low
        plus_dm.append(up if (up > down and up > 0) else 0.0)
        minus_dm.append(down if (down > up and down > 0) else 0.0)
        tr = max(
            candles[i].high - candles[i].low,
            abs(candles[i].high - candles[i - 1].close),
            abs(candles[i].low - candles[i - 1].close),
        )
        trs.append(tr)

    def _wilder(values: list[float]) -> list[float]:
        out = [sum(values[:period])]
        for i in range(period, len(values)):
            out.append(out[-1] - out[-1] / period + values[i])
        return out

    atr_s = _wilder(trs)
    pdm_s = _wilder(plus_dm)
    mdm_s = _wilder(minus_dm)
    dxs: list[float] = []
    for atr_v, pdm_v, mdm_v in zip(atr_s, pdm_s, mdm_s):
        if atr_v == 0:
            continue
        pdi = 100 * pdm_v / atr_v
        mdi = 100 * mdm_v / atr_v
        denom = pdi + mdi
        dxs.append(100 * abs(pdi - mdi) / denom if denom else 0.0)
    if len(dxs) < period:
        return sum(dxs) / len(dxs) if dxs else None
    return sum(dxs[-period:]) / period


def support_resistance(candles: list[Candle], lookback: int = 50) -> tuple[float, float]:
    """Support (plus bas) et résistance (plus haut) sur la fenêtre récente."""
    window = candles[-lookback:] if len(candles) >= lookback else candles
    return min(c.low for c in window), max(c.high for c in window)


def obv(candles: list[Candle]) -> list[float]:
    """On-Balance Volume (OBV)."""
    if not candles:
        return []
    out = [candles[0].volume]
    for i in range(1, len(candles)):
        c = candles[i]
        prev_close = candles[i - 1].close
        if c.close > prev_close:
            out.append(out[-1] + c.volume)
        elif c.close < prev_close:
            out.append(out[-1] - c.volume)
        else:
            out.append(out[-1])
    return out


def vwap(candles: list[Candle]) -> float | None:
    """Volume Weighted Average Price (VWAP) sur la période donnée."""
    if not candles:
        return None
    cum_vol = 0.0
    cum_pv = 0.0
    for c in candles:
        typ_price = (c.high + c.low + c.close) / 3
        cum_pv += typ_price * c.volume
        cum_vol += c.volume
    if cum_vol == 0:
        return None
    return cum_pv / cum_vol


def acc_dist(candles: list[Candle]) -> list[float]:
    """Accumulation/Distribution Line."""
    if not candles:
        return []
    out = []
    ad = 0.0
    for c in candles:
        if c.high == c.low:
            clv = 0.0
        else:
            clv = ((c.close - c.low) - (c.high - c.close)) / (c.high - c.low)
        ad += clv * c.volume
        out.append(ad)
    return out

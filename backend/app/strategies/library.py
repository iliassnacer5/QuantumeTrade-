"""Bibliothèque de stratégies — 5 stratégies à edge réel, déterministes et backtestables.

Chaque stratégie : `fn(candles) -> Direction` (signal d'ENTRÉE sur la dernière bougie). Le moteur de
backtest applique ensuite SL/TP (ATR), frais/slippage et stops dynamiques de façon homogène.

1. Ichimoku Kinko Hyo  — système de tendance complet et auto-filtrant.
2. Multi-timeframe EMA/structure — alignement tendance base + unité supérieure (resample).
3. Volume Profile / VWAP — acceptation du prix vs valeur (POC + VWAP) ; edge institutionnel.
4. SMC / Order Blocks — Smart Money : cassure de structure (BOS) + zones institutionnelles.
5. Mean reversion Z-score — retour à la moyenne statistique (décorrélé des autres).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from app.domain import indicators as ind
from app.domain.indicators import Candle
from app.models.signal import Direction


@dataclass(frozen=True)
class Strategy:
    id: str
    name: str
    category: str       # tendance | retour-moyenne | volume | smart-money | cassure
    description: str
    fn: Callable[[list[Candle]], Direction]
    markets: tuple[str, ...] = ("crypto", "forex", "stock", "commodity")  # marchés où la stratégie a du sens


def _closes(c: list[Candle]) -> list[float]:
    return [x.close for x in c]


def _resample(candles: list[Candle], factor: int) -> list[Candle]:
    """Agrège `factor` bougies en une (approxime une unité de temps supérieure)."""
    out: list[Candle] = []
    for i in range(0, len(candles) - factor + 1, factor):
        grp = candles[i:i + factor]
        out.append(Candle(grp[0].open, max(g.high for g in grp), min(g.low for g in grp),
                          grp[-1].close, sum(g.volume for g in grp)))
    return out


# ------------------------------- 1. ICHIMOKU -------------------------------
def get_ichimoku_params(market_type: str) -> tuple[int, int, int]:
    """Périodes Ichimoku adaptées au marché (tenkan, kijun, senkou_b).

    Forex/actions (5j/sem) : 9/26/52 (standard). Crypto (24/7) : 20/60/120 — mais ces périodes
    longues exigent >120 bougies, incompatibles avec la fenêtre de backtest actuelle (60). On
    retombe donc sur le standard si l'historique fourni est insuffisant (A/B test = fenêtre élargie)."""
    if market_type == "crypto":
        return (20, 60, 120)
    return (9, 26, 52)


def ichimoku(candles: list[Candle], market_type: str = "crypto") -> Direction:
    """Tendance Ichimoku : prix vs nuage (Senkou A/B) + croisement Tenkan/Kijun."""
    t, k, b = get_ichimoku_params(market_type)
    # Repli sur le standard si l'historique ne couvre pas Senkou B (ex. crypto 120 vs fenêtre 60).
    if len(candles) < b:
        t, k, b = (9, 26, 52)
    if len(candles) < b:
        return Direction.HOLD

    def mid(n: int) -> float:
        w = candles[-n:]
        return (max(g.high for g in w) + min(g.low for g in w)) / 2

    tenkan = mid(t)       # ligne de conversion
    kijun = mid(k)        # ligne de base
    span_a = (tenkan + kijun) / 2
    span_b = mid(b)
    price = candles[-1].close
    cloud_top, cloud_bot = max(span_a, span_b), min(span_a, span_b)

    if price > cloud_top and tenkan > kijun:
        return Direction.BUY
    if price < cloud_bot and tenkan < kijun:
        return Direction.SELL
    return Direction.HOLD


# --------------------- 2. MULTI-TIMEFRAME EMA / STRUCTURE ---------------------
def mtf_ema(candles: list[Candle]) -> Direction:
    """Tendance confirmée sur 2 unités de temps : EMA 20/50 sur la base ET sur l'unité supérieure."""
    if len(candles) < 60:
        return Direction.HOLD
    base = _closes(candles)
    b_fast, b_slow = ind.ema(base, 20)[-1], ind.ema(base, 50)[-1]
    htf = _resample(candles, 3)  # ~3× l'unité de temps
    if len(htf) < 20:
        return Direction.HOLD
    h = _closes(htf)
    h_fast, h_slow = ind.ema(h, 10)[-1], ind.ema(h, 20)[-1]

    if b_fast > b_slow and h_fast > h_slow:
        return Direction.BUY
    if b_fast < b_slow and h_fast < h_slow:
        return Direction.SELL
    return Direction.HOLD


# ----------------------- 3. VOLUME PROFILE / VWAP -----------------------
def volume_vwap(candles: list[Candle]) -> Direction:
    """Acceptation du prix : au-dessus du VWAP ET du POC (niveau de plus fort volume) -> haussier."""
    if len(candles) < 30 or sum(c.volume for c in candles) <= 0:
        return Direction.HOLD  # marché sans volume (ex. forex) -> pas de signal
    vwap_val = ind.vwap(candles)
    if vwap_val is None:
        return Direction.HOLD

    lo = min(c.low for c in candles)
    hi = max(c.high for c in candles)
    if hi <= lo:
        return Direction.HOLD
    nb = 20
    size = (hi - lo) / nb
    buckets = [0.0] * nb
    for c in candles:
        idx = min(nb - 1, int(((c.high + c.low) / 2 - lo) / size))
        buckets[idx] += c.volume
    poc = lo + (max(range(nb), key=lambda i: buckets[i]) + 0.5) * size  # point of control
    price = candles[-1].close

    if price > vwap_val and price > poc:
        return Direction.BUY
    if price < vwap_val and price < poc:
        return Direction.SELL
    return Direction.HOLD


# ----------------------- 4. SMC / ORDER BLOCKS -----------------------
def smc_order_blocks(candles: list[Candle], lookback: int = 20) -> Direction:
    """Smart Money : cassure de structure (Break of Structure) du plus haut/bas de range."""
    if len(candles) < lookback + 5:
        return Direction.HOLD
    recent = candles[-lookback - 1:-1]  # exclut la bougie courante
    swing_high = max(c.high for c in recent)
    swing_low = min(c.low for c in recent)
    price, prev = candles[-1].close, candles[-2].close

    # Confirmation d'impulsion : la dernière bougie est franche dans le sens de la cassure.
    body = abs(candles[-1].close - candles[-1].open)
    rng = max(candles[-1].high - candles[-1].low, 1e-9)
    impulsive = body > 0.5 * rng

    if prev <= swing_high and price > swing_high and impulsive:
        return Direction.BUY   # BOS haussière
    if prev >= swing_low and price < swing_low and impulsive:
        return Direction.SELL  # BOS baissière
    return Direction.HOLD


def _trend_sign(candles: list[Candle]) -> int:
    """Tendance de fond via EMA longue (EMA200 si dispo, sinon EMA50) : +1 haussier, -1 baissier, 0."""
    closes = _closes(candles)
    if len(closes) < 50:
        return 0
    slow = ind.ema(closes, 200)[-1] if len(closes) >= 200 else ind.ema(closes, 50)[-1]
    price = closes[-1]
    if price > slow * 1.001:
        return 1
    if price < slow * 0.999:
        return -1
    return 0


# ----------------------- 5. MEAN REVERSION Z-SCORE -----------------------
def zscore_reversion(candles: list[Candle], period: int = 20, z: float = 2.0) -> Direction:
    """Retour à la moyenne DANS LE SENS DE LA TENDANCE : achat des creux en tendance haussière,
    vente des excès en tendance baissière. Évite d'acheter un couteau qui tombe."""
    closes = _closes(candles)
    if len(closes) < period:
        return Direction.HOLD
    window = closes[-period:]
    mean = sum(window) / period
    std = (sum((x - mean) ** 2 for x in window) / period) ** 0.5
    if std <= 0:
        return Direction.HOLD
    z_val = (closes[-1] - mean) / std
    trend = _trend_sign(candles)
    if z_val < -z and trend >= 0:   # survendu ET pas en tendance baissière
        return Direction.BUY
    if z_val > z and trend <= 0:    # suracheté ET pas en tendance haussière
        return Direction.SELL
    return Direction.HOLD


# ----------------------- 6. GAP FILL (actions) -----------------------
def gap_fill(candles: list[Candle]) -> Direction:
    """Comblement de gap (ACTIONS) : un gap d'ouverture >0,3% se comble ~70% du temps.

    Gap haussier non comblé -> SELL vers le close précédent ; gap baissier -> BUY. Contrarien."""
    if len(candles) < 3:
        return Direction.HOLD
    prev, last = candles[-2], candles[-1]
    if prev.close <= 0:
        return Direction.HOLD
    gap = (last.open - prev.close) / prev.close
    if abs(gap) < 0.003:
        return Direction.HOLD
    if gap > 0 and last.close > prev.close:   # gap up toujours ouvert -> fade vers le comblement
        return Direction.SELL
    if gap < 0 and last.close < prev.close:   # gap down toujours ouvert -> rebond vers le comblement
        return Direction.BUY
    return Direction.HOLD


# ----------------------- 7. SQUEEZE BREAKOUT (forex/crypto) -----------------------
def squeeze_breakout(candles: list[Candle]) -> Direction:
    """Cassure de COMPRESSION : range des 8 dernières bougies < 1,2×ATR (squeeze), puis cassure.

    Version déterministe du « breakout de session » forex : la volatilité se contracte
    (session calme) puis explose — on prend la cassure du range compressé."""
    if len(candles) < 30:
        return Direction.HOLD
    atr_v = ind.atr(candles, 14) or 0.0
    if atr_v <= 0:
        return Direction.HOLD
    window = candles[-9:-1]  # range compressé (exclut la bougie courante)
    hi = max(c.high for c in window)
    lo = min(c.low for c in window)
    if (hi - lo) > 1.2 * atr_v:
        return Direction.HOLD  # pas de compression -> pas de setup
    price = candles[-1].close
    if price > hi:
        return Direction.BUY
    if price < lo:
        return Direction.SELL
    return Direction.HOLD


# ----------------------- 8. ROUTEUR DE RÉGIME -----------------------
def regime_router(candles: list[Candle]) -> Direction:
    """Adapte la stratégie au RÉGIME de marché : tendance (ADX>25) -> suivi de tendance (MTF EMA) ;
    range (ADX<20) -> retour à la moyenne (Z-score) ; zone grise (20-25) -> pas de trade.

    Principe : chaque famille de stratégie ne gagne que dans son régime. Le whipsaw vient de
    trader la tendance en range et le mean-reversion en tendance."""
    adx = ind.adx(candles, 14) or 0.0
    if adx > 25:
        return mtf_ema(candles)
    if adx < 20:
        return zscore_reversion(candles)
    return Direction.HOLD


REGISTRY: dict[str, Strategy] = {
    s.id: s
    for s in [
        Strategy("ichimoku", "Ichimoku Kinko Hyo", "tendance",
                 "Système de tendance complet : prix vs nuage + croisement Tenkan/Kijun. Auto-filtrant.", ichimoku),
        Strategy("mtf_ema", "Multi-timeframe EMA / structure", "tendance",
                 "Tendance confirmée sur 2 unités de temps (EMA 20/50 base + unité supérieure). Réduit les faux signaux. "
                 "★ Meilleur combo mesuré : 4h.", mtf_ema),
        Strategy("volume_vwap", "Volume Profile / VWAP", "volume",
                 "Acceptation du prix vs valeur : au-dessus du VWAP et du POC (niveau de plus fort volume). "
                 "Nécessite du volume réel.", volume_vwap, markets=("crypto", "stock", "commodity")),
        Strategy("smc_ob", "SMC / Order Blocks", "smart-money",
                 "Smart Money Concepts : cassure de structure (BOS) du range avec bougie impulsive.", smc_order_blocks),
        Strategy("zscore", "Mean reversion Z-score", "retour-moyenne",
                 "Retour à la moyenne statistique (±2σ) DANS le sens de la tendance de fond. Décorrélé des autres.", zscore_reversion),
        Strategy("gap_fill", "Gap Fill (comblement de gap)", "retour-moyenne",
                 "Actions : un gap d'ouverture >0,3% se comble ~70% du temps — on trade le comblement.", gap_fill,
                 markets=("stock", "commodity")),
        Strategy("squeeze_breakout", "Squeeze Breakout (compression)", "cassure",
                 "Forex/crypto : la volatilité se contracte (session calme) puis explose — cassure du range compressé.",
                 squeeze_breakout, markets=("forex", "crypto", "commodity")),
        Strategy("regime_router", "Routeur de régime (adaptatif)", "tendance",
                 "Choisit la stratégie selon le régime : tendance (ADX>25) → MTF EMA ; range (ADX<20) → Z-score.", regime_router),
    ]
}


def get_strategy(strategy_id: str) -> Strategy | None:
    return REGISTRY.get(strategy_id)


def list_strategies() -> list[dict]:
    return [
        {"id": s.id, "name": s.name, "category": s.category, "description": s.description,
         "markets": list(s.markets)}
        for s in REGISTRY.values()
    ]

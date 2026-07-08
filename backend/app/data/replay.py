"""Rejeu de prix : un trade (entrée + SL + TP) a-t-il gagné / perdu / est-il encore ouvert ?

Logique partagée entre le paper trading (clôture auto des positions) et le Journal d'apprentissage
(résolution automatique des signaux). Rejoue les bougies depuis l'entrée et détecte le premier
niveau touché (SL prioritaire si les deux le sont dans la même bougie — hypothèse prudente).
"""

from __future__ import annotations

from app.data import ohlcv as _ohlcv


def iso_to_unix(iso: str | None) -> float:
    if not iso:
        return 0.0
    try:
        from datetime import datetime
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except Exception:  # noqa: BLE001
        return 0.0


async def replay_outcome(
    symbol: str, direction: str, entry: float,
    stop_loss: float | None, take_profit: float | None,
    since_iso: str | None, interval: str = "1h",
) -> tuple[str, float, float | None]:
    """Retourne (outcome, exit_price, closed_ts) avec outcome ∈ {won, lost, open}."""
    is_buy = str(direction).lower() in ("buy", "long")
    rows = await _ohlcv.get_ohlcv(symbol, interval=interval, limit=400)
    since = iso_to_unix(since_iso)
    after = [r for r in rows if r.get("time", 0) >= since] or rows[-1:]
    for r in after:
        hi, lo = r["high"], r["low"]
        hit_sl = stop_loss is not None and (lo <= stop_loss if is_buy else hi >= stop_loss)
        hit_tp = take_profit is not None and (hi >= take_profit if is_buy else lo <= take_profit)
        if hit_sl:  # prudent : le stop l'emporte
            return "lost", stop_loss, r["time"]
        if hit_tp:
            return "won", take_profit, r["time"]
    last = after[-1]["close"] if after else entry
    return "open", last, None

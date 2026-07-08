"""Carte de l'edge (Phase B du plan maître) — industrialise la découverte d'edge.

Sweep systématique : chaque stratégie × chaque symbole (4 marchés) × chaque timeframe (4h/1d) passe
au walk-forward avec frais. Chaque combo est classé :
  🟢 green  : alpha > 0 ET profit factor ≥ 1,2 (exploitable)
  🟡 yellow : alpha > 0 (à surveiller)
  🔴 red    : pas d'edge (à éviter)

Le résultat est stocké (record `edge_map`) avec un `green_streak` par combo : un edge qui clignote
n'est pas un edge — l'auto-trading papier ne prend que les combos verts stables.

Efficacité : les bougies sont chargées UNE fois par (symbole, timeframe) puis réutilisées pour
toutes les stratégies (paramètre `preloaded` du walk-forward).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

# Univers balayé (compact : le sweep doit rester < quelques minutes).
UNIVERSE: dict[str, list[str]] = {
    "crypto": ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT"],
    "forex": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD"],
    "stock": ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"],
    "commodity": ["XAU/USD", "XAG/USD"],
}
TIMEFRAMES = ["4h", "1d"]


# Un « vert » à 1-2 trades est du bruit (PF 10 / win 100% par chance) : échantillon minimal requis.
MIN_TRADES_GREEN = 8


def _classify(alpha: float, pf: float, trades: int = 0) -> str:
    if alpha > 0 and pf >= 1.2 and trades >= MIN_TRADES_GREEN:
        return "green"
    if alpha > 0:
        return "yellow"  # inclut les combos prometteurs mais à échantillon insuffisant
    return "red"


async def _preload(symbol: str, timeframe: str):
    """Charge une fois les bougies horodatées d'un symbole (repli synthétique tracé)."""
    from app.data.ohlcv import get_ohlcv
    from app.domain.indicators import Candle

    rows = await get_ohlcv(symbol, interval=timeframe, limit=1000)
    data_real = len(rows) >= 100
    candles = [
        Candle(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0),
               timestamp=datetime.fromtimestamp(r["time"], UTC))
        for r in rows
    ] if data_real else []
    return candles, data_real


async def run_edge_sweep(store, timeframes: list[str] | None = None,
                         markets: list[str] | None = None) -> dict:
    """Exécute le sweep complet et persiste la carte. Retourne le payload stocké."""
    from app.backtest.walkforward import walk_forward
    from app.strategies import list_strategies

    tfs = timeframes or TIMEFRAMES
    strategies = list_strategies()
    rows: list[dict] = []

    for market, symbols in UNIVERSE.items():
        if markets and market not in markets:
            continue
        fitting = [s for s in strategies if market in (s.get("markets") or [])]
        for symbol in symbols:
            for tf in tfs:
                try:
                    preloaded = await _preload(symbol, tf)
                except Exception as exc:  # noqa: BLE001 — un symbole HS ne bloque pas le sweep
                    logger.warning("Edge sweep : données %s %s indisponibles (%s)", symbol, tf, exc)
                    continue
                for s in fitting:
                    try:
                        r = await walk_forward(symbol, tf, folds=4, strategy_id=s["id"], preloaded=preloaded)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Edge sweep : %s %s %s échoué (%s)", s["id"], symbol, tf, exc)
                        continue
                    alpha = r.get("avg_alpha_pct", 0.0) or 0.0
                    pf = r.get("avg_profit_factor", 0.0) or 0.0
                    n_trades = r.get("total_trades", 0) or 0
                    rows.append({
                        "strategy": s["id"], "strategy_name": s["name"], "symbol": symbol,
                        "market": market, "timeframe": tf,
                        "alpha": alpha, "pf": pf, "win": r.get("avg_win_rate", 0.0),
                        "trades": n_trades, "verdict": r.get("verdict"),
                        "data_real": bool(r.get("data_real", preloaded[1])),
                        "status": _classify(alpha, pf, n_trades),
                    })

    # Stabilité : un combo vert AUJOURD'HUI ET la fois précédente vaut plus qu'un vert isolé.
    prev = (store.records.get("edge_map", "latest") or {}).get("rows", [])
    prev_streak = {f"{p['strategy']}|{p['symbol']}|{p['timeframe']}": p.get("green_streak", 0) for p in prev}
    for row in rows:
        key = f"{row['strategy']}|{row['symbol']}|{row['timeframe']}"
        row["green_streak"] = (prev_streak.get(key, 0) + 1) if row["status"] == "green" else 0

    greens = [r for r in rows if r["status"] == "green"]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "rows": sorted(rows, key=lambda r: (r["alpha"], r["pf"]), reverse=True),
        "greens": len(greens),
        "yellows": len([r for r in rows if r["status"] == "yellow"]),
        "reds": len([r for r in rows if r["status"] == "red"]),
        "note": (f"✅ {len(greens)} combo(s) exploitables (alpha>0, PF≥1,2 out-of-sample)." if greens
                 else "⚠️ Aucun combo vert actuellement — s'abstenir est la bonne décision."),
    }
    store.records.put("edge_map", "latest", payload)
    store.records.put("edge_map", datetime.now(UTC).date().isoformat(), payload)
    logger.info("Edge sweep terminé : %d combos (%d verts)", len(rows), len(greens))
    return payload


def get_edge_map(store) -> dict | None:
    return store.records.get("edge_map", "latest")


def is_combo_green(store, strategy_id: str, symbol: str, min_streak: int = 1) -> bool:
    """Vrai si (stratégie, symbole) est vert sur AU MOINS un timeframe balayé, avec la stabilité requise.

    Utilisé par l'auto-trading papier : on ne trade automatiquement que là où l'edge est prouvé."""
    latest = get_edge_map(store)
    if not latest:
        return False
    return any(
        r["strategy"] == strategy_id and r["symbol"] == symbol
        and r["status"] == "green" and r.get("green_streak", 0) >= min_streak
        for r in latest.get("rows", [])
    )

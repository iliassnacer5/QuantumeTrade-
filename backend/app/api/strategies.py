"""Stratégies de trading — bibliothèque, backtest, validation walk-forward et sélection.

Permet de comparer les stratégies (Ichimoku, MTF EMA, Volume/VWAP, SMC/Order Blocks, Z-score) sur
données réelles, d'en valider la robustesse (walk-forward), d'en CHOISIR une, et de générer un
signal actionnable à partir de la stratégie choisie sur le marché en direct.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import current_user, store_dep
from app.core.plans import require_feature
from app.domain import indicators as ind
from app.domain.risk import RiskParams, compute_levels
from app.models.entities import User
from app.models.signal import Direction
from app.repositories.store import AppStore
from app.strategies import get_strategy, list_strategies

router = APIRouter(prefix="/api/strategies", tags=["strategies"])

_SEL = "strategy_choice"


@router.get("")
async def strategies(_user: User = Depends(current_user)) -> dict:
    """Liste les stratégies disponibles (id, nom, famille, description)."""
    return {"strategies": list_strategies()}


@router.post("/backtest")
async def backtest_strategy(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    strategy: str = "ichimoku",
    user: User = Depends(require_feature("backtesting")),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Backteste une stratégie sur l'historique réel et renvoie les métriques + courbe d'équité."""
    from app.api.backtest import _load_history
    from app.backtest.engine import run_backtest
    from app.backtest.schemas import BacktestConfig

    strat = get_strategy(strategy)
    if strat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Stratégie inconnue : {strategy}")
    candles = await _load_history(symbol, timeframe, limit=600)
    cfg = BacktestConfig(
        symbol=symbol, timeframe=timeframe,
        start_time=candles[0].timestamp, end_time=candles[-1].timestamp, initial_capital=10000,
    )
    report = await run_backtest(cfg, candles, tenant_id=user.tenant_id, strategy=strat.fn)
    m = report.metrics
    return {
        "strategy": strategy, "symbol": symbol, "timeframe": timeframe,
        "metrics": {
            "trades": m.total_trades, "win_rate": round(m.win_rate * 100, 1),
            "profit_factor": m.profit_factor, "total_pnl_pct": m.total_pnl_pct,
            "max_drawdown_pct": m.max_drawdown_pct, "sharpe": m.sharpe_ratio,
            "expectancy": m.expectancy,
        },
        "benchmark_pnl_pct": report.benchmark_pnl_pct,
        "alpha_pct": report.alpha_pct,
        "cost_pct_per_side": report.cost_pct_per_side,
        "equity_curve": [{"t": p.timestamp.isoformat(), "equity": p.equity} for p in report.equity_curve[::5]],
    }


@router.post("/compare")
async def compare_strategies(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    user: User = Depends(require_feature("backtesting")),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Backteste TOUTES les stratégies sur `symbol` (frais inclus) et désigne la meilleure.

    Classement par alpha (vs buy & hold) puis profit factor. La « meilleure » n'est conseillée que
    si son alpha est positif — sinon l'honnêteté commande de s'abstenir."""
    from app.api.backtest import _load_history
    from app.backtest.engine import run_backtest
    from app.backtest.schemas import BacktestConfig

    candles = await _load_history(symbol, timeframe, limit=600)
    cfg = BacktestConfig(symbol=symbol, timeframe=timeframe,
                         start_time=candles[0].timestamp, end_time=candles[-1].timestamp, initial_capital=10000)
    rows = []
    for s in list_strategies():
        try:
            rep = await run_backtest(cfg, candles, tenant_id=user.tenant_id, strategy=get_strategy(s["id"]).fn)
            m = rep.metrics
            rows.append({
                "id": s["id"], "name": s["name"], "category": s["category"],
                "trades": m.total_trades, "win_rate": round(m.win_rate * 100, 1),
                "profit_factor": m.profit_factor, "pnl_pct": m.total_pnl_pct,
                "alpha_pct": rep.alpha_pct, "max_drawdown_pct": m.max_drawdown_pct, "sharpe": m.sharpe_ratio,
            })
        except Exception:  # noqa: BLE001
            continue
    rows.sort(key=lambda r: (r["alpha_pct"], r["profit_factor"]), reverse=True)
    best = rows[0] if rows else None
    recommended = best if (best and best["alpha_pct"] > 0 and best["profit_factor"] > 1) else None
    return {
        "symbol": symbol, "timeframe": timeframe, "ranking": rows,
        "best": best, "recommended": recommended,
        "note": ("✅ %s a un edge positif sur cette période." % recommended["name"]) if recommended
                else "⚠️ Aucune stratégie ne bat le buy & hold après frais ici — mieux vaut s'abstenir ou tester un autre marché/timeframe.",
    }


@router.post("/walk-forward")
async def walk_forward_strategy(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    strategy: str = "ichimoku",
    folds: int = 4,
    _user: User = Depends(require_feature("backtesting")),
) -> dict:
    """Validation out-of-sample d'une stratégie (verdict robuste/fragile/non prouvé)."""
    from app.backtest.walkforward import walk_forward as run_wf

    try:
        return await run_wf(symbol, timeframe, folds=max(2, min(folds, 6)), strategy_id=strategy)
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc


_MULTI_SYMBOLS = {
    "crypto": ("BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT"),
    "forex": ("EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "EUR/GBP"),
    "stock": ("AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL"),
    "commodity": ("XAU/USD", "XAG/USD"),
}


@router.post("/validate-multi")
async def validate_multi(
    strategy: str = "ichimoku",
    timeframe: str = "1h",
    market: str = "crypto",
    _user: User = Depends(require_feature("backtesting")),
) -> dict:
    """Valide une stratégie sur PLUSIEURS symboles d'un MARCHÉ — une stratégie fiable doit tenir partout.

    `market` : crypto | forex | stock. Évite de confondre un edge réel avec un coup de chance."""
    from app.backtest.walkforward import walk_forward as run_wf

    if get_strategy(strategy) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Stratégie inconnue : {strategy}")
    results = []
    for sym in _MULTI_SYMBOLS.get(market, _MULTI_SYMBOLS["crypto"]):
        try:
            results.append(await run_wf(sym, timeframe, folds=4, strategy_id=strategy))
        except Exception:  # noqa: BLE001 — un symbole ne doit pas bloquer les autres
            continue
    robust = sum(1 for r in results if r["verdict"] == "robuste")
    fragile = sum(1 for r in results if r["verdict"] == "fragile")
    beats = sum(1 for r in results if r.get("avg_alpha_pct", 0) > 0)
    n = len(results)
    if robust >= max(1, n // 2):
        verdict = "✅ Fiable sur plusieurs marchés"
    elif robust + fragile >= max(1, n // 2):
        verdict = "⚠️ Variable selon les marchés"
    else:
        verdict = "🔴 Ne tient pas — pas de fiabilité multi-marchés"
    return {
        "strategy": strategy, "timeframe": timeframe, "market": market, "symbols": n,
        "robust": robust, "fragile": fragile, "beats_hold": beats,
        "verdict": verdict, "results": results,
    }


@router.post("/auto-trade")
async def set_auto_trade(
    enabled: bool = True,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Active/désactive le FORWARD TEST automatique : chaque signal de ta stratégie active ouvre
    un trade papier (risque 1%, SL/TP, clôture auto). Le Portefeuille virtuel juge sur la durée."""
    store.records.put("auto_trade", user.tenant_id, {"enabled": enabled}, tenant_id=user.tenant_id)
    return {"auto_trade": enabled}


@router.get("/auto-trade")
async def get_auto_trade(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    return {"auto_trade": bool((store.records.get("auto_trade", user.tenant_id) or {}).get("enabled"))}


@router.post("/select")
async def select_strategy(
    strategy: str,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Choisit la stratégie active de l'utilisateur (pour générer des signaux)."""
    if get_strategy(strategy) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Stratégie inconnue : {strategy}")
    store.records.put(_SEL, user.tenant_id, {"strategy": strategy}, tenant_id=user.tenant_id)
    return {"selected": strategy}


@router.get("/selected")
async def selected_strategy(
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    rec = store.records.get(_SEL, user.tenant_id)
    return {"selected": (rec or {}).get("strategy")}


@router.post("/signal")
async def strategy_signal(
    symbol: str = "BTC/USDT",
    timeframe: str = "1h",
    strategy: str | None = None,
    user: User = Depends(current_user),
    store: AppStore = Depends(store_dep),
) -> dict:
    """Génère un signal actionnable (direction + SL/TP) à partir d'une stratégie sur le marché LIVE."""
    from app.data import markets

    sid = strategy or (store.records.get(_SEL, user.tenant_id) or {}).get("strategy") or "ichimoku"
    strat = get_strategy(sid)
    if strat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Stratégie inconnue : {sid}")

    candles = await markets.load_candles(symbol, interval=timeframe, limit=200)
    direction = strat.fn(candles)
    entry = candles[-1].close
    source = markets.data_source(symbol)
    if direction == Direction.HOLD:
        return {"strategy": sid, "symbol": symbol, "direction": "HOLD", "entry": round(entry, 8),
                "rationale": f"{strat.name} : pas de signal d'entrée actuellement.", "data_source": source}

    risk = RiskParams(capital=user.capital, risk_per_trade_pct=1.0)
    atr_v = ind.atr(candles, 14) or (entry * 0.01)
    levels = compute_levels(direction, entry, atr_v, risk)
    return {
        "strategy": sid, "name": strat.name, "symbol": symbol, "timeframe": timeframe,
        "direction": direction.value, "entry": round(entry, 8),
        "stop_loss": levels.stop_loss, "take_profit_1": levels.take_profit_1,
        "take_profit_2": levels.take_profit_2, "risk_reward": levels.risk_reward,
        "position_size": levels.position_size, "data_source": source,
        "generated_at": datetime.now(UTC).isoformat(),
        "rationale": f"{strat.name} ({strat.category}) → {direction.value}.",
    }

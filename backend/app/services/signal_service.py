"""Service de génération de signaux — la boucle de valeur du MVP.

Données (Binance ou synthétique) -> Agents (Technique + Sentiment) -> Master -> Signal Engine
-> persistance -> diffusion WebSocket -> alerte.
"""

from __future__ import annotations

import logging

from app.data import macro as macro_data_mod, markets, news as news_mod
from app.domain.indicators import Candle
from app.domain.risk import RiskParams
from app.models.entities import User
from app.models.signal import Timeframe
from app.models.signal import SignalCard
from app.realtime import bus
from app.repositories.store import AppStore
from app.services import journal_service, risk_service
from app.signal_engine.engine import generate_signal
from app.alerts.notifier import notify_signal

logger = logging.getLogger(__name__)

# Profil de risque -> % du capital risqué par trade
_RISK_PCT = {"conservative": 0.5, "moderate": 1.0, "aggressive": 2.0}

_TF_INTERVAL = {
    Timeframe.SCALP: "5m",
    Timeframe.INTRADAY: "15m",
    Timeframe.SWING: "1h",
    Timeframe.POSITION: "4h",
}


async def _load_candles(symbol: str, timeframe: Timeframe) -> list[Candle]:
    """Charge les bougies selon la classe d'actif (crypto/actions/forex), repli synthétique inclus."""
    return await markets.load_candles(symbol, interval=_TF_INTERVAL.get(timeframe, "1h"), limit=200)


_TF_TO_INTERVAL = {"scalp": "5m", "intraday": "15m", "swing": "1h", "position": "4h"}


async def backtest_metrics(symbol: str, interval: str, limit: int = 500) -> dict | None:
    """Backtest déterministe de la paire et renvoie les KPI (ou None si indisponible)."""
    from datetime import UTC, datetime

    from app.backtest.engine import run_backtest
    from app.backtest.schemas import BacktestConfig
    from app.data.ohlcv import get_ohlcv
    from app.domain.indicators import Candle

    try:
        rows = await get_ohlcv(symbol, interval, limit=limit)
        candles = [
            Candle(r["open"], r["high"], r["low"], r["close"], r.get("volume", 0.0),
                   timestamp=datetime.fromtimestamp(r["time"], UTC))
            for r in rows
        ]
        if len(candles) < 100:
            return None
        cfg = BacktestConfig(symbol=symbol, timeframe=interval,
                             start_time=candles[0].timestamp, end_time=candles[-1].timestamp, initial_capital=10000)
        m = (await run_backtest(cfg, candles, tenant_id="bt")).metrics
        return {
            "trades": m.total_trades, "win_rate": round(m.win_rate * 100, 1),
            "profit_factor": m.profit_factor, "total_pnl_pct": m.total_pnl_pct,
            "max_drawdown_pct": m.max_drawdown_pct, "sharpe": m.sharpe_ratio,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Backtest %s échoué (%s)", symbol, exc)
        return None


async def daily_picks(per_market: int = 3, classes: tuple[str, ...] = ("crypto", "forex", "stock")) -> list[dict]:
    """Sélection quotidienne : par marché, les setups haute-conviction CONFIRMÉS par backtest.

    Critères retenus : ★ haute-conviction (ADX>25, tendance forte) ET backtest fiable
    (taux de réussite > 55 % et profit factor > 1,3 sur ≥ 5 trades). C'est la liste de trades
    « fiables et bien backtestés » à surveiller dans chaque marché.
    """
    out: list[dict] = []
    for cls in classes:
        scanned = await scan_market(asset_class=cls, timeframe="1h", limit=14, high_conviction_only=True)
        kept = 0
        for cand in scanned:  # déjà triés par conviction
            bt = await backtest_metrics(cand["symbol"], "1h")
            if not bt or bt["trades"] < 5:
                continue
            reliable = bt["win_rate"] > 55 and bt["profit_factor"] > 1.3
            if not reliable:
                continue
            out.append({
                "symbol": cand["symbol"], "asset_class": cls, "direction": cand["direction"],
                "price": cand["price"], "adx": cand["adx"], "rsi": cand["rsi"],
                "trend": cand["trend"], "conviction": cand["conviction"], "backtest": bt,
            })
            kept += 1
            if kept >= per_market:
                break
    return out


async def verify_signal(
    symbol: str, timeframe: str, *,
    confidence: int = 0, consensus_pct: int = 0, risk_reward: float = 0.0,
    mtf_aligned: int = 0, mtf_total: int = 0, adx: float | None = None, direction: str = "HOLD",
) -> dict:
    """Vérifie la fiabilité d'un signal : backtest de la paire + checklist du trader.

    Combine une validation quantitative (backtest historique) et les critères de qualité du signal
    (confiance, consensus, multi-timeframe, R/R, force de tendance) en un verdict ✅/⚠️/🔴.
    """
    interval = _TF_TO_INTERVAL.get(timeframe, timeframe if "m" in timeframe or "h" in timeframe or "d" in timeframe else "1h")
    bt = await backtest_metrics(symbol, interval)

    checks: list[dict] = []
    if bt and bt["trades"] >= 5:
        checks.append({"label": "Backtest : taux de réussite > 55 %", "pass": bt["win_rate"] > 55, "value": f"{bt['win_rate']}%"})
        checks.append({"label": "Backtest : profit factor > 1,3", "pass": bt["profit_factor"] > 1.3, "value": bt["profit_factor"]})
    checks.append({"label": "Confiance ≥ 70 %", "pass": confidence >= 70, "value": f"{confidence}%"})
    checks.append({"label": "Consensus ≥ 70 %", "pass": consensus_pct >= 70, "value": f"{consensus_pct}%"})
    if mtf_total:
        checks.append({"label": "Multi-timeframe ≥ 2/3 alignés", "pass": mtf_aligned >= 2, "value": f"{mtf_aligned}/{mtf_total}"})
    checks.append({"label": "R/R ≥ 1,5", "pass": risk_reward >= 1.5, "value": f"1 : {risk_reward}"})
    checks.append({"label": "Tendance forte (ADX > 25)", "pass": (adx or 0) > 25, "value": round(adx, 1) if adx else "—"})

    passed = sum(1 for c in checks if c["pass"])
    total = len(checks)
    if direction == "HOLD":
        verdict = "skip"
    elif passed >= total - 1:
        verdict = "strong"
    elif passed >= total / 2:
        verdict = "moderate"
    else:
        verdict = "weak"
    return {"verdict": verdict, "passed": passed, "total": total, "checks": checks, "backtest": bt}


async def scan_market(
    asset_class: str | None = None,
    timeframe: str = "1h",
    limit: int = 20,
    high_conviction_only: bool = False,
) -> list[dict]:
    """Scanne un marché et classe les symboles par conviction (rapide : analyse technique).

    Retourne TOUS les symboles analysés, triés par score de conviction, avec un flag
    `high_conviction` (ADX>25 + tendance franche). Le multi-timeframe complet et les news sont
    calculés à la demande quand l'utilisateur ouvre un symbole (« Analyser »).
    """
    from app.data import symbols as symbols_catalog
    from app.domain import ta
    from app.models.signal import Direction

    universe = symbols_catalog.search(asset_class=asset_class, limit=limit)
    results: list[dict] = []
    for item in universe:
        sym = item["symbol"]
        try:
            candles = await markets.load_candles(sym, interval=timeframe, limit=200)
            if len(candles) < 60:
                continue
            a = ta.analyze(candles)
            m = a["metrics"]
            adx = m.get("adx", 0) or 0
            direction = Direction.BUY if a["score"] > 0.12 else Direction.SELL if a["score"] < -0.12 else Direction.HOLD
            high_conv = direction != Direction.HOLD and ta.is_high_conviction(a["score"], adx, item["asset_class"])
            conviction = round(abs(a["score"]) * (1 + adx / 50), 3)
            results.append({
                "symbol": sym,
                "asset_class": item["asset_class"],
                "direction": direction.value,
                "score": a["score"],
                "adx": round(adx, 1),
                "adx_state": m.get("adx_state"),
                "trend": m.get("trend"),
                "rsi": m.get("rsi"),
                "price": m.get("price"),
                "conviction": conviction,
                "high_conviction": high_conv,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("Scan %s échoué (%s)", sym, exc)
    if high_conviction_only:
        results = [r for r in results if r["high_conviction"]]
    results.sort(key=lambda r: (r["high_conviction"], r["conviction"]), reverse=True)
    return results


async def generate_for_user(
    user: User,
    store: AppStore,
    *,
    asset: str,
    timeframe: Timeframe = Timeframe.SWING,
    notify: bool = True,
) -> SignalCard:
    """Génère, persiste, diffuse et notifie un signal pour un utilisateur."""
    candles = await _load_candles(asset, timeframe)
    news_items = await news_mod.fetch_news(asset)
    macro_ctx = await macro_data_mod.fetch_macro_data()

    risk = RiskParams(
        capital=user.capital,
        risk_per_trade_pct=_RISK_PCT.get(user.risk_profile, 1.0),
    )

    # Contexte de risque courant (exposition) + apprentissage Journal (poids dynamiques).
    # L'agent risque se base sur l'exposition RÉELLE (ordres exécutés), pas sur l'accumulation des
    # analyses générées — sinon générer des signaux pénaliserait injustement la confiance.
    risk_context = {"exposure_pct": risk_service.real_exposure_pct(user, store), "drawdown_pct": 0.0}
    journal_mult = journal_service.compute_multipliers(store, user.tenant_id)

    card = await generate_signal(
        asset=asset,
        candles=candles,
        news=news_items,
        risk=risk,
        timeframe=timeframe,
        macro_data=macro_ctx,
        risk_context=risk_context,
        journal_multipliers=journal_mult,
    )

    # Avertissement de risque non bloquant (exposition simulée) sur la carte.
    warn = risk_service.generation_warning(user, store)
    if warn:
        card.risk_warning = warn if not card.risk_warning else f"{card.risk_warning} {warn}"

    # Confirmation multi-timeframe (1h/4h/1j) + marqueur haute-conviction.
    from app.signal_engine import mtf
    card.mtf = await mtf.confirm(asset, card.direction)
    adx = card.metrics.get("adx")
    card.high_conviction = bool(
        card.direction.value != "HOLD"
        and adx and adx > 25
        and card.consensus_pct >= 70
        and card.mtf.get("aligned", 0) >= 2
    )

    # Persistance (isolée par tenant)
    payload = card.model_dump(mode="json")
    stored = store.signals.add(user.tenant_id, payload)
    payload["id"] = stored.id

    # Observabilité (Phase 5)
    from app.core import metrics
    metrics.inc("signals_generated_total", direction=card.direction.value if hasattr(card.direction, "value") else str(card.direction))

    # Boucle d'apprentissage : enregistre l'issue (open) + scores d'agents pour le Journal.
    journal_service.record_signal(store, user.tenant_id, card, stored.id)

    # Copy-trading (Phase 4) : si l'utilisateur est un trader public, réplique vers ses suiveurs.
    try:
        from app.services import copytrading_service
        await copytrading_service.on_leader_signal(store, user.tenant_id, card)
    except Exception as exc:  # noqa: BLE001 — la copie ne doit jamais casser la génération
        logger.warning("Copy-trading fan-out échoué (%s)", exc)

    # Diffusion temps réel (Redis pub/sub si actif, sinon hub mémoire) + alerte
    await bus.publish(user.tenant_id, {"type": "signal", "data": payload})
    if notify:
        await notify_signal(
            card,
            email=user.email if user.alert_email else None,
            telegram_chat_id=user.telegram_chat_id if user.alert_telegram else None,
            webhook_url=user.webhook_url if user.alert_webhook else None,
            sms_to=user.phone if user.alert_sms else None,
            push_token=user.push_token,
        )

    return card

"""M3 — Signal Engine.

Orchestre TOUS les agents (Technique, Sentiment, Pattern, Fondamental, Macro, Risque), applique
l'arbitrage du Master Agent (pondération dynamique + apprentissage Journal), calcule les niveaux de
risque (déterministe) et produit une `SignalCard` consolidée, explicable et avec le détail des agents.
"""

from __future__ import annotations

from app.agents import fundamental, macro as macro_agent, pattern, risk_agent, sentiment, technical, volume
from app.agents import master
from app.agents.base import AgentOutput
from app.agents.sentiment import NewsItem
from app.domain import indicators as ind
from app.domain.indicators import Candle
from app.domain.risk import RiskParams, compute_levels
from app.models.signal import Direction, SignalCard, Timeframe


def _breakdown(outputs: list[AgentOutput]) -> list[dict]:
    """Détail COMPLET par agent : score, confiance, justification ET données structurées.

    Les `details` (figures détectées, Fear & Greed, funding, pénalité risque…) sont conservés pour
    que la prédiction soit consultable « en détail du détail ». Le technique est allégé (ses
    métriques complètes sont déjà dans card.metrics, inutile de les dupliquer)."""
    out = []
    for o in outputs:
        d = dict(getattr(o, "details", None) or {})
        if o.name == "technical":
            d = {k: d[k] for k in ("funding_rate", "btc_lead", "spx_regime", "gap_pct", "dxy", "expert") if k in d}
        out.append({"name": o.name, "score": o.score, "confidence": o.confidence,
                    "rationale": o.rationale, "details": d})
    return out


async def generate_signal(
    *,
    asset: str,
    candles: list[Candle],
    news: list[NewsItem] | None = None,
    fear_greed: int | None = None,
    risk: RiskParams,
    timeframe: Timeframe = Timeframe.SWING,
    weights: dict[str, float] | None = None,
    ratios: dict | None = None,
    macro_data: dict | None = None,
    risk_context: dict | None = None,
    journal_multipliers: dict[str, float] | None = None,
) -> SignalCard:
    """Produit une Signal Card à partir des données de marché, sentiment, fondamentaux et macro."""
    news = news or []
    # Sans Fear & Greed externe, on dérive un indice de marché (momentum/volatilité) pour que
    # l'agent sentiment contribue au lieu de rester muet ("pas de news").
    if fear_greed is None:
        from app.domain import ta as _ta
        fear_greed = _ta.fear_greed_proxy(candles)

    # 1. Agents — l'agent technique est routé vers l'expert du marché (contexte = classe d'actif).
    from app.data.markets import asset_class as _asset_class
    _ctx = {"market_type": _asset_class(asset), "symbol": asset}
    outputs: list[AgentOutput] = [
        await technical.run(candles, symbol=asset, context=_ctx),
        await volume.run(candles),
        await sentiment.run(news, fear_greed),
        await pattern.run(candles),
    ]
    # L'agent fondamental n'a de sens que pour les ACTIONS (ou si des ratios sont fournis).
    # (Avant : condition inversée qui l'activait sur la crypto et l'omettait sur les actions.)
    from app.data.markets import asset_class as _asset_class
    if ratios is not None or _asset_class(asset) == "stock":
        outputs.append(await fundamental.run(asset, ratios))
    if macro_data is not None:
        outputs.append(await macro_agent.run(macro_data))

    risk_out = None
    if risk_context is not None:
        risk_out = risk_agent.run_sync(
            exposure_pct=risk_context.get("exposure_pct", 0.0),
            drawdown_pct=risk_context.get("drawdown_pct", 0.0),
            correlation=risk_context.get("correlation", 0.0),
            returns=risk_context.get("returns"),
        )
        outputs.append(risk_out)

    # 2. Arbitrage Master (pondération dynamique + apprentissage)
    decision = master.decide(
        outputs, weights=weights, journal_multipliers=journal_multipliers, risk_output=risk_out
    )

    entry = candles[-1].close
    atr_val = ind.atr(candles, 14) or (entry * 0.01)
    breakdown = _breakdown(outputs)
    # Tableau de bord des indicateurs : exposé depuis l'agent technique (détails = métriques ta).
    metrics = next((o.details for o in outputs if o.name == "technical"), {}) or {}
    # La PESÉE du Master (transparence totale) : poids effectifs par agent, score combiné, seuils.
    metrics["master_decision"] = {
        "score": decision.score,           # score combiné pondéré [-1..+1]
        "threshold": 0.12,                 # BUY si > +0.12 ; SELL si < -0.12 ; sinon HOLD
        "consensus": decision.consensus,
        "conflict": decision.conflict,
        "weights_used": decision.weights_used,  # poids effectif de chaque agent dans la décision
    }

    if decision.direction == Direction.HOLD:
        return SignalCard(
            asset=asset,
            direction=Direction.HOLD,
            entry=round(entry, 8),
            stop_loss=round(entry, 8),
            take_profit_1=round(entry, 8),
            risk_reward=0.0,
            confidence=decision.confidence,
            timeframe=timeframe,
            rationale=decision.rationale,
            agents=breakdown,
            metrics=metrics,
            consensus_pct=decision.consensus,
        )

    levels = compute_levels(decision.direction, entry, atr_val, risk)
    return SignalCard(
        asset=asset,
        direction=decision.direction,
        entry=round(entry, 8),
        stop_loss=levels.stop_loss,
        take_profit_1=levels.take_profit_1,
        take_profit_2=levels.take_profit_2,
        take_profit_3=levels.take_profit_3,
        risk_reward=levels.risk_reward,
        confidence=decision.confidence,
        timeframe=timeframe,
        rationale=decision.rationale,
        position_size=levels.position_size,
        position_value=levels.position_value,
        risk_amount=levels.risk_amount,
        agents=breakdown,
        metrics=metrics,
        consensus_pct=decision.consensus,
    )

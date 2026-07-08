# QUANTUM TRADE AI — Explication complète du projet (état actuel)

> Document de référence détaillé : architecture, agents, pipelines complets, technologies,
> fonctionnalités. Reflète l'état **actuel** du code. Principe directeur : **mesurer la fiabilité,
> pas la promettre**. Aide à la décision, jamais un conseil en investissement.

---

## 1. Vue d'ensemble

Plateforme SaaS de **trading multi-agents IA**, multi-marchés (crypto, forex, actions). Elle
transforme des données de marché temps réel en signaux explicables, permet de les tester en paper
trading avec un portefeuille virtuel, mesure honnêtement leur fiabilité (walk-forward avec frais) et
apprend en continu de leurs résultats.

**Le fil rouge : l'honnêteté.** Données réelles vs synthétiques signalées ; frais + slippage inclus
dans les backtests ; benchmark « buy & hold » ; validation out-of-sample ; cohérence garantie entre
le scanner et l'analyse détaillée ; aucun edge survendu.

---

## 2. Stack technique

| Couche | Technologies |
|---|---|
| **Frontend** | Next.js (App Router) · React · TypeScript · TailwindCSS |
| **Backend** | FastAPI (Python 3.11+) · async natif · Pydantic v2 |
| **IA / LLM** | LiteLLM (routeur Claude + Gemini) · failover · cache TTL. LLM **jamais** pour le risque (déterministe). |
| **Données** | PostgreSQL + TimescaleDB · Redis (cache/pub-sub) · Redpanda/Kafka |
| **Temps réel** | WebSocket Binance (ingestion) + WebSocket clients (diffusion) · hub par tenant |
| **Mobile** | React Native (Expo) |
| **Paiement** | Stripe |
| **Infra** | Docker Compose (postgres, redis, redpanda, backend, frontend) · images de prod |
| **Sécurité** | JWT/OAuth2 · MFA TOTP · argon2 · clés broker chiffrées (AEAD) · isolation multi-tenant |
| **Observabilité** | Prometheus `/metrics` · X-Request-ID · Sentry optionnel |

**Sources externes** : Binance (crypto REST+WS), Yahoo (actions/forex, VIX, DXY, SPX), Finnhub (news +
fondamentaux + earnings), NewsAPI/newsdata (news), FRED (taux/inflation), CoinGecko (dominance BTC),
alternative.me (Fear & Greed).

---

## 3. Architecture du dépôt

```
backend/app/
├── agents/
│   ├── technical.py       ROUTEUR -> expert du marché OU analyse générique
│   ├── crypto_expert.py   RSI conditionnel (ADX), funding contrarien, BTC lead
│   ├── forex_expert.py    filtre DXY sur paires USD
│   ├── stocks_expert.py   régime SPX (risk-off), gap fill
│   ├── volume.py          OBV/VWAP/divergences (neutre si volume=0)
│   ├── sentiment.py       news (LLM/lexique) + Fear & Greed
│   ├── pattern.py         figures chandeliers + vision Gemini (option)
│   ├── fundamental.py     ratios PER/croissance/dette/marge (actions)
│   ├── macro.py           VIX/taux/inflation -> régime risk-on/off
│   ├── risk_agent.py      exposition/drawdown — 100% déterministe
│   ├── master.py          arbitrage : pondération + anti-dilution + bonus expert ×1.3
│   ├── journal.py         apprentissage : fiabilité par agent (par volume)
│   └── llm.py             routeur LiteLLM + cache + failover
├── signal_engine/
│   ├── engine.py          orchestration agents -> SignalCard
│   ├── mtf.py             confirmation multi-timeframe (1h/4h/1j)
│   └── quality.py         filtre qualité + anti-couteau + scores contexte/timing
├── data/
│   ├── markets.py         load_candles (source tracée : live/real/synthetic)
│   ├── binance.py         REST + WebSocket ; yahoo.py, ohlcv.py
│   ├── news.py, macro.py, fundamentals.py
│   ├── cross_asset.py     funding, BTC lead, DXY, régime SPX, dominance BTC
│   ├── economic_calendar.py  blackout earnings + FOMC
│   ├── replay.py          rejeu de prix (gagné/perdu/ouvert) — PARTAGÉ
│   ├── market_stream.py   ingestion live (cache + push)
│   └── sessions.py, symbols.py, synthetic.py
├── strategies/library.py  5 stratégies (Ichimoku, MTF EMA, VWAP, SMC, Z-score)
├── backtest/
│   ├── engine.py          moteur (frais, slippage, stops dynamiques)
│   ├── metrics.py         win-rate, PF, Sharpe, drawdown, expectancy
│   └── walkforward.py     validation out-of-sample + validate_expert_agent
├── services/
│   ├── signal_service.py  generate_for_user, scan_market, finalize_decision, daily_picks, verify
│   ├── execution_service.py  paper trading + clôture auto/manuelle + garde-fous
│   ├── wallet_service.py  portefeuille virtuel
│   ├── journal_service.py apprentissage (par marché)
│   ├── scheduler.py       boucles de fond (digest, positions, learning, alertes)
│   └── strategy_alert_service, risk_service, portfolio_service, copilot_service
├── api/                   routeurs FastAPI (un par domaine)
├── realtime/  bus.py (Redis) · hub.py (WebSocket)
├── core/      config, security, plans, crypto, deps, metrics
└── repositories/  store (mémoire ou SQL)

frontend/app/  dashboard, scanner, copilot, strategies, backtest, track-record,
               daily, execution (paper), wallet, journal, agents, settings…
```

---

## 4. PIPELINE CŒUR — génération d'un signal

Point d'entrée : `signal_service.generate_for_user(user, asset, timeframe)`.

```
1) DONNÉES
   load_candles(asset, tf) -> source tracée (live/real/synthetic)
     crypto : cache WS -> REST Binance -> synthétique
     actions: Alpaca(clé) -> Yahoo -> synthétique
     forex  : OANDA(clé) -> Yahoo -> synthétique
   + news (Finnhub/NewsAPI) + macro (VIX/FRED) + ratios (Finnhub, actions)

2) LES 8 AGENTS (parallèle ; déterministes + LLM optionnel)
   technical -> ROUTEUR :
      crypto_expert  : RSI atténué si ADX>25 ; funding contrarien ; BTC lead
      forex_expert   : filtre DXY (paires USD)
      stocks_expert  : régime SPX + gap fill
   volume (neutre si volume=0) · sentiment · pattern · fundamental (actions)
   macro · risk (déterministe)
   -> chaque agent : score [-1..+1] + confiance + justification

3) MASTER (arbitrage)
   poids base × multiplicateurs Journal (PAR MARCHÉ) × régime macro
   + BONUS ×1.3 agent EXPERT · anti-dilution (|score|≥0.05)
   -> direction (BUY>0.12 / SELL<-0.12 / HOLD) + confiance

4) NIVEAUX (déterministe) : entrée=close ; SL=1.5×ATR ; TP=2.5/4/6×ATR ; R/R ; taille

5) DÉCISION FINALE (finalize_decision — SOURCE UNIQUE)
   0) Gate ÉVÉNEMENTIEL : blackout earnings/FOMC -> HOLD [EVENT_LOCK]
   1) Gate MULTI-TIMEFRAME : ≥2/3 unités alignées sinon HOLD
   2) Filtre QUALITÉ : confiance≥62, ADX≥22, R/R≥1.5
                     + ANTI-COUTEAU : pas de BUY sous l'EMA longue
   3) Flag ★ HAUTE-CONVICTION (ADX>25 + consensus≥70 + MTF≥2)
   + scores context_score / timing_score

6) SORTIE : SignalCard persistée -> WebSocket -> notif -> Journal -> copy-trading
```

**Garantie** : `finalize_decision` est utilisée à l'identique par l'analyse ET le scanner (même
contexte utilisateur) → aucune divergence possible sur les candidats évalués.

---

## 5. Les 8 agents (résumé)

| Agent | Rôle | LLM ? |
|---|---|---|
| technical (routeur) | Aiguille vers l'expert marché | commentaire |
| crypto_expert | RSI/ADX, funding, BTC lead | non |
| forex_expert | filtre DXY | non |
| stocks_expert | régime SPX, gap | non |
| volume | OBV/VWAP/divergences (neutre sans volume) | non |
| sentiment | news + Fear & Greed | oui (scoring) |
| pattern | figures + vision | oui (vision) |
| fundamental | ratios réels Finnhub (actions) | non |
| macro | VIX/taux/inflation | non |
| risk | exposition/drawdown | **jamais** |
| master | arbitrage + bonus expert | non |
| journal | fiabilité par agent/marché | non |

---

## 6. Pipelines de fond (`scheduler.py`, boucles asyncio)

| Pipeline | Rôle | Fréquence |
|---|---|---|
| Ingestion live (`market_stream`) | 8 WS Binance → cache frais + push prix | continu |
| Moniteur de positions | clôture auto paper au SL/TP + P&L | ~60 s |
| Apprentissage | résout signaux ouverts → poids par agent/marché | ~5 min |
| Alertes stratégie | nouveau signal → push/email/Telegram | ~10 min |
| Digest quotidien | trades du jour + résumé | 1×/jour |

**Rejeu partagé** (`data/replay.py`) : « gagné/perdu/ouvert » (SL prioritaire) — utilisé par la
clôture paper ET la résolution auto du Journal.

---

## 7. Backtest & validation

```
run_backtest : rejoue chaque bougie
  entrée = stratégie OU moteur agents (anti-couteau)
  SL/TP ATR ; STOPS DYNAMIQUES (breakeven +0.3R après +1R ; trailing 3×ATR en profit)
  FRAIS + SLIPPAGE 0,15%/côté ; BENCHMARK buy&hold + ALPHA

walk_forward : N segments successifs indépendants -> robuste/fragile/non prouvé
  (robuste = régulier + PF≥1.3 + alpha>0 APRÈS frais)

validate_expert_agent(market, symbols) : effet des agents experts par marché
compare_strategies(symbol) : backteste TOUTES les stratégies, classe par alpha/PF, désigne la meilleure
```

---

## 8. Les 5 stratégies

1. **Ichimoku** (tendance) — prix vs nuage + Tenkan/Kijun.
2. **Multi-timeframe EMA/structure** (tendance) — EMA base + unité supérieure (resample).
3. **Volume Profile / VWAP** (volume) — prix vs VWAP + POC.
4. **SMC / Order Blocks** (smart money) — cassure de structure + impulsion.
5. **Mean reversion Z-score** (retour-moyenne) — ±2σ, **dans le sens de la tendance** (anti-couteau).

---

## 9. Fonctionnalités par page

Dashboard · Scanner (★ = analyse, top 8 consolidés) · Copilot (agentique) · Stratégies (backtest +
walk-forward + comparateur) · Backtest · Track Record · Trades du jour (gradué + timeframe) · Paper
Trading (clôture auto/manuelle) · 💰 Portefeuille virtuel · Journal (apprentissage) · Copy-trading ·
Marketplace · White-label · Plans · Exécution réelle (Alpaca, KYC+Elite) · Paramètres · i18n.

---

## 10. Chaîne d'honnêteté

- Source tracée : live / real / synthetic + badge UI + **refus de trader sur synthétique**.
- Volume neutre sans volume (forex) ; fondamental réel (actions).
- Backtests frais + slippage + benchmark buy & hold.
- Cross-asset (funding, DXY, SPX, dominance BTC) avec **repli gracieux**.
- Verify checklist : verdict + interprétation honnête (« edge non prouvé »).

---

## 11. Apprentissage continu par marché

Signal → Journal (open + scores) → rejeu prix → win/loss → `compute_weight_multipliers(market)` →
le Master applique les poids appris **par marché** (un agent mauvais en forex ne pénalise plus la
crypto). Pondération par volume (confiance bayésienne n/(n+12)).

---

## 12. Sécurité, plans, multi-tenant

Isolation `tenant_id` · plans Free→Enterprise avec gating · MFA, clés chiffrées, rate limiting, audit
log, KYC pour le réel, garde-fous exposition/positions configurables.

---

## 13. État actuel & limites honnêtes

**Opérationnel** : temps réel crypto, paper + portefeuille, apprentissage par marché, 5 stratégies +
agents experts, validation honnête, copilot, filtre événementiel, comparateur. **~166 tests verts.**

**Limites (la vérité)** :
- **Aucun edge prouvé** : « fragile/non prouvé » après frais — l'outil le mesure, ne le cache pas.
- **Live = crypto only** ; forex/actions = Yahoo/synthétique sans clés Alpaca/OANDA.
- **Funding rate** : API Binance futures parfois bloquée (repli neutre).
- **Exécution réelle** : seul le paper est branché (réel = clés + KYC).
- **Cohérence scanner** : garantie sur le top 8 ; le reste = pré-filtre « à analyser ».
- **Légal** : Phase 0 (statut éditeur, CGU, AMF/MiFID) à traiter avant usage par des tiers.

---

## 14. En une phrase

Données temps réel → 8 agents IA (dont experts par marché) → décision consolidée, gatée et
explicable → paper trading → mesure honnête (portefeuille + walk-forward avec frais) → apprentissage
par marché. Une plateforme **complète et honnête** qui **mesure** un edge plutôt qu'elle n'en garantit un.

---

*Aide à la décision, pas un conseil en investissement. Le trading comporte un risque élevé de perte ;
les performances passées ne préjugent pas des résultats futurs.*

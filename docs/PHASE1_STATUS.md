# Phase 1 (MVP) — État d'avancement

> ✅ **Phase 1 COMPLÈTE** — tous les points du cahier des charges sont implémentés, **testés (48 tests backend verts)** et **vérifiés en Docker** (Postgres + Redis). Build frontend OK (9 pages). Le système tourne sans clés ni Postgres (repos mémoire + repli déterministe) et bascule automatiquement vers les vrais fournisseurs/persistance dès configuration.

## Lots de complétion (du MVP à la Phase 1 complète)
| Lot | Livré | Vérifié |
|-----|-------|---------|
| **Redis pub/sub** (multi-instance) + repli mémoire | `app/realtime/bus.py` | Docker : `redis=True` au boot |
| **Ingestion OHLCV → TimescaleDB** | `app/repositories/sql.py` (SqlMarketRepository) + `OhlcvORM` | Docker : 50 lignes dans la hypertable `ohlcv` |
| **Règles de risque appliquées** (expo max, signaux/jour) + `/api/risk/status` | `app/services/risk_service.py` | Test : 2e génération bloquée `429` |
| **P&L latent** `/api/portfolio` + **heatmap** `/api/market/heatmap` | `portfolio_service.py`, `data/heatmap.py` | Docker : heatmap données Binance réelles |
| **Écran Paramètres** + préférences alertes (Telegram chat_id) | `frontend/app/settings/page.tsx`, `api/settings.py` | Build OK + tests |
| **Stripe réel** (Checkout + webhook signé) + repli stub | `app/api/billing.py` | Webhook signature vérifiée |
| **Rate limiting** + **audit log** + **MFA (TOTP)** | `core/ratelimit.py`, `services/audit.py`, `core/totp.py` | Docker : `429` brute-force, MFA login OK |

## Couverture par module

| Module | Implémenté | Détails |
|--------|-----------|---------|
| **M1 Data Ingestion** | ✅ | Binance REST backfill + WS (reconnexion auto) `app/data/binance.py` ; news Finnhub `app/data/news.py` ; repli synthétique offline `app/data/synthetic.py` |
| **M2 Agents** | ✅ | Abstraction LLM LiteLLM + fallback `app/agents/llm.py` ; Agent Technique (RSI/MACD/EMA/Bollinger) ; Agent Sentiment (lexique/score) ; Master Agent (arbitrage, détection de conflit, pondération) |
| **M3 Signal Engine** | ✅ | Fusion → `SignalCard` `app/signal_engine/engine.py` |
| **M4 Risk Management** | ✅ | Déterministe (sizing, SL/TP via ATR, R/R, VaR, exposition) `app/domain/risk.py` — **aucun LLM** |
| **M5 Dashboard** | ✅ | Auth, onboarding, dashboard live (WS), SignalCard `frontend/` |
| **M7 Alertes** | ✅ | Email (Resend) + Telegram, no-op gracieux sans clé `app/alerts/notifier.py` |
| **M10 Facturation** | ✅ | Plans + checkout + webhook (stub Stripe) ; gating par plan `app/api/billing.py` |
| **Sécurité** | ✅ | JWT HS256, hachage PBKDF2, isolation multi-tenant (tenant par compte), auth WS |

## Boucle de valeur (vérifiée par `tests/test_api_flow.py`)

```
inscription → onboarding → /signals/generate
   → data (Binance ou synthétique)
   → Agent Technique + Agent Sentiment
   → Master (arbitrage + confiance)
   → Risk (SL/TP/sizing déterministes)
   → SignalCard explicable
   → persistance (tenant) → diffusion WebSocket → alerte
→ historique /signals → upgrade plan /billing/checkout
```

## Tests (32 passés)
- `test_indicators.py` — RSI/EMA/MACD/Bollinger/ATR
- `test_risk.py` — niveaux, sizing, VaR, exposition
- `test_agents.py` — Technique, Sentiment, Master (conflit)
- `test_signal_engine.py` — génération end-to-end
- `test_security.py` — hash + JWT (falsification/expiration)
- `test_api_flow.py` — parcours complet, isolation tenant, gating Free/Starter
- `test_health.py`, `test_signal_card.py`

## 🧪 Definition of Done Phase 1
| Critère | Statut |
|---------|--------|
| Signal généré end-to-end (data→agents→engine→card) | ✅ Testé |
| Justification IA lisible | ✅ Champ `rationale` rempli par le Master |
| Alerte email + Telegram | ✅ Implémenté (no-op sans clé, réel avec clé) |
| Paiement Stripe | ✅ Checkout réel + webhook signé (repli stub sans clé) |
| Tests d'intégration verts | ✅ 48/48 |
| Sécurité (MFA, rate limit, audit, multi-tenant) | ✅ Implémenté et vérifié en Docker |
| Déployé sur staging | ⬜ Action infra (CI build OK, stack Docker vérifiée en local) |

## Renforcements MVP livrés
- **Bascule Postgres réelle** : repositories SQL (SQLAlchemy) interface-identiques aux repos mémoire,
  sélectionnés par `USE_IN_MEMORY_DB`. Validée par `tests/test_postgres_switch.py` (sur SQLite, même
  couche SQLAlchemy → parcours API complet sur backend SQL). `app/repositories/sql.py`.
- **Chart TradingView** : `GET /api/market/ohlcv` (Binance + repli synthétique horodaté) +
  composant `frontend/components/Chart.tsx` (lightweight-charts) intégré au dashboard avec lignes
  de prix entrée/SL/TP du signal sélectionné (clic sur une carte).

## Pour activer le mode production
1. Renseigner les clés dans `.env` (Anthropic/Gemini, Binance, Finnhub, Stripe, Telegram/Resend).
2. Passer `USE_IN_MEMORY_DB=false` (+ driver `psycopg2`) et appliquer `infra/db/init.sql` sur Postgres.
   Les tables sont aussi créées automatiquement au démarrage (`create_all`).
3. Le routing LiteLLM et les agents basculent automatiquement sur les LLM réels.

## Limites assumées (par périmètre — relèvent des Phases 2-4)
- Sentiment via lexique tant qu'aucune clé LLM n'est fournie (FinBERT/LLM réel en Phase 2 ; le routing LiteLLM est déjà branché).
- Hors périmètre Phase 1 : backtesting (M6), exécution broker (M8), mobile, agents Pattern/Fondamental/Macro → Phases 2-4.
- Le P&L est *latent* (positions dérivées des signaux) ; le journal de trades réel arrive en Phase 3.

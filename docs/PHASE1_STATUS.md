# Phase 1 (MVP) — État d'avancement

La boucle de valeur de bout en bout est implémentée, **runnable et testée** (32 tests backend verts, build frontend OK). Le système tourne **sans clés API ni Postgres** (repositories en mémoire + repli déterministe / synthétique), et bascule automatiquement vers les vrais fournisseurs dès que les clés sont configurées.

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
| Paiement Stripe | 🟡 Stub fonctionnel (gating + checkout + webhook) ; intégration Stripe réelle = brancher la clé |
| Tests d'intégration verts | ✅ 32/32 |
| Déployé sur staging | ⬜ Action infra (CI build OK) |

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

## Limites assumées du MVP (par périmètre)
- Persistance en mémoire par défaut (modèles SQLAlchemy + schéma SQL prêts pour la bascule).
- Sentiment via lexique en l'absence de LLM (FinBERT/LLM en Phase 2).
- Pas encore : backtesting (M6), exécution broker (M8), mobile, autres agents → Phases 2-4.

# Architecture technique — Quantum Trade AI

## Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────┐
│  CLIENTS : Web (Next.js) · Mobile (React Native) · API/SDK    │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS / WebSocket
┌───────────────────────────▼──────────────────────────────────┐
│  API GATEWAY (FastAPI) — auth OAuth2+MFA · rate limit ·       │
│  routage multi-tenant                                         │
└──────┬───────────────────┬───────────────────┬────────────────┘
       │                   │                   │
┌──────▼──────┐    ┌────────▼────────┐   ┌──────▼──────────┐
│ DATA (M1)   │    │ AGENTS (M2)     │   │ BILLING (M10)   │
│ WS Binance  │──▶ │ LangGraph       │   │ Stripe          │
│ Normalize   │    │ Master + agents │   │                 │
│ TimescaleDB │    │ Signal Eng (M3) │   └─────────────────┘
└──────┬──────┘    │ Risk Mgmt (M4)  │
       │           └────────┬────────┘
       ▼                    ▼
┌──────────────────────────────────────────────────────────────┐
│ PERSISTENCE : PostgreSQL+TimescaleDB · Redis · Kafka/Redpanda │
└──────────────────────────────────────────────────────────────┘
```

## Composants

| Service | Techno | Port (dev) | Rôle |
|---------|--------|-----------|------|
| `frontend` | Next.js | 3000 | UI web |
| `backend` | FastAPI | 8000 | API + agents + engines |
| `postgres` | TimescaleDB pg16 | 5432 | Données relationnelles + séries temps |
| `redis` | Redis 7 | 6379 | Cache + pub/sub temps réel |
| `redpanda` | Kafka-compatible | 9092 | Pipeline de données (dev) |

## Pipeline de données (cf. cahier des charges §4.3)

1. **Ingestion** — connecteurs WebSocket collectent OHLCV + news en temps réel
2. **Normalisation** — nettoyage, standardisation, stockage en séries temporelles
3. **Analyse** — les agents IA traitent en parallèle et produisent des scores
4. **Fusion** — le Signal Engine consolide en un signal pondéré
5. **Diffusion** — push vers dashboard (WebSocket) + canaux d'alerte
6. **Exécution** *(optionnel, Phase 4)* — transmission au broker via API
7. **Journalisation** — archivage de chaque trade/signal pour l'apprentissage

## Découpage backend (modules du cahier des charges)

| Dossier | Module | Statut |
|---------|--------|--------|
| `app/data/` | M1 Data Ingestion | Phase 1 |
| `app/agents/` | M2 Agents IA | Phase 1 (2 agents) → Phase 2 (7) |
| `app/signal_engine/` | M3 Signal Engine | Phase 1 |
| `app/risk/` | M4 Risk Management (déterministe) | Phase 1 |
| `app/api/` | API REST/WS (auth, signals, billing) | Phase 1+ |
| `app/billing/` | M10 Facturation Stripe | Phase 1 |
| `app/backtest/` | M6 Backtesting | Phase 2 |
| `app/alerts/` | M7 Alertes | Phase 1 (email/Telegram) → Phase 2 |
| `app/execution/` | M8 Exécution broker | Phase 4 |

## Principes structurants

- **Découplage LLM** : tout passe par LiteLLM → failover + routing Claude/Gemini sans couplage fournisseur.
- **Risque = déterministe** : SL/TP/VaR calculés en Python pur, jamais via un LLM.
- **Multi-tenant strict** : `tenant_id` sur chaque table métier, isolation des données.
- **Sorties structurées** : schémas Pydantic stricts (`SignalCard`) comme contrat inter-couches.
- **12-factor** : toute la config vient de l'environnement.

## Sécurité (cf. §4.4)

TLS 1.3 en transit · AES-256 au repos · MFA + OAuth2 · isolation multi-tenant · clés broker chiffrées et révocables · audit log · conformité OWASP Top 10 · pentests réguliers.

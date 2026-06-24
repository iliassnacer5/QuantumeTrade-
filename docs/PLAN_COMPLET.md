# 🚀 QUANTUM TRADE AI — Plan de réalisation complet (A → Z)

> Plan d'exécution opérationnel pour construire la plateforme SaaS de trading multi-agents IA, du dépôt vide à la production.
> Basé sur le cahier des charges v1.0 (Juin 2026).

---

## 0. Comment utiliser ce document

Ce plan est découpé en **phases séquentielles**. Chaque phase contient :
- 🎯 **Objectif** : ce qu'on prouve / livre à la fin
- 📦 **Livrables** : artefacts concrets
- ✅ **Tâches** : checklist actionnable
- 🧪 **Critères de sortie** (Definition of Done)

**Règle d'or : ne JAMAIS sauter la Phase 0 (cadrage juridique + setup).** Sur une plateforme de trading, l'erreur la plus coûteuse est juridique, pas technique.

**Principe directeur : MVP d'abord.** On livre une boucle de valeur minimale (1 marché crypto → 2 agents → signal explicable → dashboard) avant d'élargir.

---

## 1. Vue d'ensemble : les 6 grandes étapes

| Étape | Nom | Durée estimée | Résultat |
|-------|-----|---------------|----------|
| **P0** | Fondations (juridique, setup, archi) | 2-4 sem | Repo prêt, cadre légal clair, maquettes |
| **P1** | MVP (la boucle de valeur) | 8-12 sem | Signal crypto fiable + dashboard + auth + paiement |
| **P2** | Tous les agents + backtesting | 8 sem | 7 agents, multi-marchés, alertes multicanal |
| **P3** | Mobile + Copilot + journal | 8 sem | Apps mobiles, chat IA, plans complets |
| **P4** | Exécution broker + copy-trading | 8-12 sem | Trading auto (paper→réel), marketplace |
| **P5** | Scale & white-label | Continu | Multi-tenant avancé, international |

---

## 2. Architecture cible (rappel technique)

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENTS                               │
│   Web (Next.js)   │   Mobile (React Native)   │   API/SDK    │
└───────────────────┴───────────────┬───────────────┴──────────┘
                                     │ HTTPS / WebSocket
┌────────────────────────────────────▼─────────────────────────┐
│                      API GATEWAY (FastAPI)                    │
│   Auth (OAuth2+MFA) │ Rate limit │ Multi-tenant routing       │
└──────┬─────────────────┬──────────────────┬───────────────────┘
       │                 │                  │
┌──────▼──────┐  ┌────────▼────────┐  ┌──────▼──────────┐
│ DATA LAYER  │  │  AGENT LAYER    │  │  BILLING/USERS  │
│ (M1)        │  │  (M2 LangGraph) │  │  (M10 Stripe)   │
│ Ingestion   │  │  Master Agent   │  │                 │
│ WS connect. │→ │  + 6 sub-agents │  │                 │
│ Normalize   │  │  ↓              │  │                 │
└──────┬──────┘  │  Signal Engine  │  └─────────────────┘
       │         │  (M3)           │
       │         │  Risk Mgmt (M4) │
       │         └────────┬────────┘
       │                  │
┌──────▼──────────────────▼────────────────────────────────────┐
│  PERSISTENCE: PostgreSQL + TimescaleDB │ Redis │ Kafka/Rabbit │
└───────────────────────────────────────────────────────────────┘
```

**Stack confirmée :**
- Frontend : Next.js + React + TailwindCSS + TradingView Lightweight Charts
- Backend : FastAPI (Python 3.11+) — async natif
- Agents : LangGraph + LiteLLM (abstraction multi-LLM Claude/Gemini)
- Data : PostgreSQL + TimescaleDB (séries temps), Redis (cache/pubsub), Kafka (pipeline)
- Infra : Docker + Kubernetes sur AWS ou GCP
- Mobile : React Native (recommandé pour partage de code avec le web)

---

## PHASE 0 — FONDATIONS (2-4 semaines)

### 🎯 Objectif
Mettre en place le cadre juridique, technique et organisationnel avant d'écrire la moindre ligne de logique métier.

### 0.1 — Juridique & conformité (BLOQUANT, à lancer en J1)
- [ ] Consulter un **avocat spécialisé en droit financier** dans chaque juridiction cible (UE/AMF-ESMA, US/SEC, UK/FCA)
- [ ] Déterminer le statut : **éditeur d'outils d'analyse** (recommandé) vs conseiller en investissement (nécessite licence)
- [ ] Rédiger CGU, politique de confidentialité, clauses de non-responsabilité
- [ ] Rédiger l'**avertissement risque** affiché partout : *« Le trading comporte un risque élevé de perte. Aide à la décision, pas un conseil en investissement. »*
- [ ] Cadrer RGPD (registre des traitements, DPO si besoin)
- [ ] Anticiper KYC/AML pour la Phase 4 (connexion broker)

### 0.2 — Setup technique du dépôt
- [ ] Choisir l'organisation du code : **monorepo** (recommandé — pnpm/turborepo pour web+mobile, dossier `backend/` Python)
- [ ] Initialiser Git + branches (`main`, `develop`, feature branches) + conventions de commit
- [ ] Configurer CI/CD (GitHub Actions) : lint, tests, build, déploiement
- [ ] Mettre en place les environnements : `dev`, `staging`, `prod`
- [ ] Gestion des secrets : Vault / AWS Secrets Manager / Doppler (jamais en clair)
- [ ] Docker Compose pour le dev local (postgres+timescale, redis, kafka, backend, frontend)
- [ ] Linters/formatters : `ruff`+`black` (Python), `eslint`+`prettier` (JS/TS)
- [ ] Pre-commit hooks

### 0.3 — Design & maquettes
- [ ] Wireframes des 9 écrans clés (Onboarding, Dashboard, Signal Card, Graphique, Portefeuille, Backtesting, Journal, Copilot, Paramètres)
- [ ] Design system : dark mode, accents rouge `#E24B4A` / vert `#1D9E75`, typographie, composants
- [ ] Maquettes haute-fidélité Figma de la **Signal Card** (élément central) et du Dashboard
- [ ] Spécifier les états temps réel (loading, live update, erreur de flux)

### 0.4 — Comptes & accès fournisseurs
- [ ] Clés API Anthropic (Claude) + Google (Gemini) → via LiteLLM
- [ ] Compte data crypto : **Binance API** (MVP) + Coinbase/CCXT en backup
- [ ] Compte news/sentiment : Finnhub + NewsAPI
- [ ] Stripe (facturation) — compte + webhooks
- [ ] Cloud (AWS ou GCP) + registry Docker
- [ ] Telegram Bot (alertes MVP) + provider email (Resend/SendGrid)

### 📦 Livrables P0
Repo configuré · CI/CD verte · Docker Compose dev fonctionnel · Maquettes Figma · Avis juridique écrit · Design system

### 🧪 Definition of Done P0
`docker compose up` lance toute la stack en local · 1 endpoint `/health` répond · maquettes validées · cadre juridique documenté

---

## PHASE 1 — MVP : LA BOUCLE DE VALEUR (8-12 semaines)

### 🎯 Objectif
**Prouver la valeur centrale** : générer un signal de trading crypto **fiable et explicable**, l'afficher, et le monétiser. Un seul marché, deux agents.

> Périmètre figé : 1 marché (crypto/Binance) · 2 agents (Technique + Sentiment) · Signal Engine · Signal Card · Dashboard web · alertes email/Telegram · auth + abonnement Starter.
> **Volontairement reporté : mobile, exécution auto, autres agents.**

### 1.1 — M1 Data Ingestion (crypto only)
- [ ] Connecteur WebSocket Binance (OHLCV multi-timeframe : 1m, 5m, 15m, 1h, 4h, 1d)
- [ ] Normalisation + stockage TimescaleDB (hypertables OHLCV)
- [ ] Gestion reconnexion auto + backfill historique (REST)
- [ ] Connecteur news (Finnhub/NewsAPI) → table news
- [ ] Redis pub/sub pour diffuser les ticks aux agents
- [ ] Tests : ingestion stable 24h sans perte de données

### 1.2 — M2 Agents (les 2 du MVP) via LangGraph + LiteLLM
**Stratégie LLM MVP : Claude Sonnet 4.5 partout + LiteLLM** (simplicité, qualité, déjà découplé). Gemini ajouté en P2.
- [ ] Couche d'abstraction LiteLLM (routing, failover, suivi des coûts)
- [ ] **Agent Technique** : calcul déterministe des indicateurs en Python (RSI, MACD, EMA, Bollinger, ATR, Ichimoku via `pandas-ta`/`ta-lib`) → score directionnel ; le LLM résume/explique
- [ ] **Agent Sentiment** : NLP des news (Claude Sonnet ; option FinBERT local) → biais sentiment + Fear & Greed Index
- [ ] **Master Agent** (Claude Sonnet) : reçoit les 2 sorties, détecte conflits, pondère, produit décision **JSON structurée + justification NL**
- [ ] Schéma de sortie strict (Pydantic) : `direction, entry, sl, tp1/2/3, rr, confidence, timeframe, rationale`
- [ ] Garde-fous : validation JSON, retry, fallback failover LLM

### 1.3 — M3 Signal Engine
- [ ] Fusion pondérée des scores → signal unique
- [ ] Calcul entrée / SL / TP1-2-3 / ratio R-R / score de confiance 0-100%
- [ ] Filtrage par timeframe (scalp, intraday, swing, position)
- [ ] Persistance des signaux + diffusion Redis → WebSocket frontend

### 1.4 — M4 Risk Management (calculs déterministes Python — JAMAIS de LLM)
- [ ] Dimensionnement position selon capital + tolérance au risque (% risque par trade)
- [ ] Calcul SL/TP, R-R, VaR de base
- [ ] Règles : stop journalier, exposition max, drawdown max
- [ ] ⚠️ Ces calculs critiques ne passent jamais par un LLM (exigence du cahier des charges)

### 1.5 — M5 Dashboard web (Next.js)
- [ ] Auth (inscription/login, OAuth2, MFA, reset password)
- [ ] Onboarding : profil de risque, objectifs, marchés suivis
- [ ] **Signal Card** (composant central) avec tous les champs + justification IA
- [ ] Liste signaux live (WebSocket, mise à jour sans reload)
- [ ] Watchlist + graphique interactif (TradingView Lightweight Charts) avec annotations IA
- [ ] P&L basique + heatmap marché

### 1.6 — M7 Alertes (canaux MVP)
- [ ] Notifications email (nouveau signal, SL/TP atteint)
- [ ] Bot Telegram (push signal)
- [ ] Préférences d'alerte par utilisateur

### 1.7 — M10 Facturation (plan Starter)
- [ ] Intégration Stripe (abonnement récurrent, webhooks, factures)
- [ ] Multi-tenant : isolation stricte des données par compte
- [ ] Plans Free + Starter (29$) avec gating des features
- [ ] Page paramètres / gestion abonnement

### 1.8 — Sécurité MVP
- [ ] TLS 1.3 en transit, AES-256 au repos
- [ ] MFA, OAuth2, hash mots de passe (argon2/bcrypt)
- [ ] Isolation multi-tenant (row-level security PostgreSQL ou tenant_id systématique)
- [ ] Rate limiting + protection OWASP Top 10
- [ ] Audit log

### 📦 Livrables P1
Plateforme web fonctionnelle de bout en bout : un utilisateur s'inscrit, paie Starter, reçoit des signaux crypto explicables en live + alertes.

### 🧪 Definition of Done P1
✅ Signal généré end-to-end (data→agents→engine→card) · ✅ Justification NL lisible · ✅ Alerte email+Telegram reçue · ✅ Paiement Stripe fonctionnel · ✅ Tests d'intégration verts · ✅ Déployé sur staging

---

## PHASE 2 — TOUS LES AGENTS + BACKTESTING (8 semaines)

### 🎯 Objectif
Passer d'une démo à une vraie salle de marché IA : 7 agents, multi-marchés, validation historique.

### 2.1 — Compléter les agents (M2)
- [ ] **Agent Pattern** (vision) : reconnaissance figures chartistes → **Gemini 2.5 Pro** (vision multimodale)
- [ ] **Agent Fondamental** : ratios, résultats, événements corporate (actions) → Claude Sonnet 4.5
- [ ] **Agent Macro** : taux, inflation, géopolitique, corrélations → **Gemini 2.5 Pro + grounding Google Search**
- [ ] **Agent Risque** : exposition, drawdown, corrélation portefeuille, VaR (déterministe)
- [ ] **Agent Journal** : mémoire & apprentissage (ajustements basés sur l'historique)
- [ ] Master Agent : pondération dynamique selon régime de marché + résolution de conflits avancée

### 2.2 — Stratégie LLM hybride (Phase 2-3 du cahier des charges)
- [ ] Router via LiteLLM : **Gemini Flash** sur agents à fort volume (Sentiment, Technique) → coûts ÷5-10
- [ ] **Gemini 2.5 Pro** pour vision (Pattern) et grounding (Macro)
- [ ] Failover automatique multi-fournisseurs
- [ ] A/B testing Claude vs Gemini par agent + suivi coût/qualité

### 2.3 — Multi-marchés (M1 étendu)
- [ ] Actions/ETF : Polygon.io / Alpaca
- [ ] Forex : OANDA / Alpha Vantage
- [ ] Futures (selon priorité)
- [ ] Macro : FRED, Trading Economics
- [ ] Pipeline Kafka/RabbitMQ pour le volume

### 2.4 — M6 Backtesting
- [ ] Moteur de backtest sur historique (event-driven, pas de look-ahead bias)
- [ ] Métriques : Sharpe, win-rate, max drawdown, profit factor, expectancy
- [ ] UI configuration de stratégie + visualisation résultats
- [ ] Validation rigoureuse (la fiabilité = le track record)

### 2.5 — M7 Alertes multicanal complètes
- [ ] Push web/mobile, SMS, webhook (en plus email/Telegram)
- [ ] Configuration fine par utilisateur et par actif

### 🧪 Definition of Done P2
7 agents opérationnels · multi-marchés live · backtest reproductible avec métriques · routing LLM hybride mesuré

---

## PHASE 3 — MOBILE + COPILOT + JOURNAL + PLANS (8 semaines)

### 🎯 Objectif
Compléter l'expérience trader et ouvrir tous les plans payants.

### 3.1 — Apps mobiles (React Native) ✅
- [x] iOS + Android (Expo) : login, signaux live, génération, alertes push natives
- [x] Réutilisation maximale de la logique web (mobile/src/api.ts ≈ frontend/lib/api.ts)
- [x] Mobile-first pour alertes en mobilité (expo-notifications + push_token bout-en-bout)

### 3.2 — M5 AI Copilot (chat) ✅
- [x] Chat conversationnel (Claude/Gemini selon clés) pour interroger un actif
- [x] Accès contextuel aux données marché + sorties d'agents (réutilise le pipeline de signaux)
- [x] Streaming des réponses (SSE /api/copilot/chat) + variante /ask pour mobile

### 3.3 — M9 Journal & apprentissage ✅
- [x] Enregistrement automatique des trades (à la génération de signal)
- [x] Explication IA des trades + analyse des erreurs (/api/journal/{id}/explain)
- [x] Boucle de feedback → ajustement des pondérations (multiplicateurs appliqués par le Master)

### 3.4 — Plans Pro (79$) & Elite (199$) ✅
- [x] Gating : backtesting, Copilot, journal (Pro) ; API, copy-trading, exécution (Elite)
- [x] Gestion d'équipe / multi-utilisateurs (/api/team invite + membres par tenant)

### 🧪 Definition of Done P3
Copilot répond avec contexte ✅ · journal auto-alimenté ✅ · 4 plans actifs + gating ✅ ·
app mobile fonctionnelle ✅ (publication stores = `eas build`, hors périmètre code)

---

## PHASE 4 — EXÉCUTION BROKER + COPY-TRADING + MARKETPLACE (8-12 sem)

### 🎯 Objectif
Passer de l'aide à la décision à l'action automatisée (avec garde-fous stricts).

### 4.1 — M8 Exécution broker ✅
- [x] Connexion brokers via API (papier + Alpaca ; abstraction extensible OANDA/Binance)
- [x] **Mode papier d'abord**, puis réel après validation (KYC)
- [x] Stockage chiffré & révocable des clés API broker (crypto.py AEAD stdlib ; jamais les fonds)
- [x] KYC/AML (prérequis de l'exécution réelle)

### 4.2 — Copy-trading ✅
- [x] Suivi des top traders (leaderboard opt-in) + partage de revenus (commission)
- [x] Contrôles de risque sur les copies (allocation %, plafond/trade, seuil de confiance)

### 4.3 — Marketplace ✅
- [x] Stratégies & agents IA personnalisés à la vente (config débloquée après achat)
- [x] API payante développeurs/institutionnels (clés hashées, Elite)

### 🧪 Definition of Done P4
Exécution paper→réel sécurisée ✅ · copy-trading fonctionnel ✅ · marketplace en ligne ✅
(paiements Stripe réels + publication stores = intégrations externes hors périmètre code)

---

## PHASE 5 — SCALE & WHITE-LABEL (Continu) ✅

- [x] Offre Enterprise white-label (branding par tenant + domaine perso + résolution publique)
- [x] SLA (sondes /health/live + /health/ready), multi-comptes avancé (sièges par plan)
- [x] Expansion internationale (i18n fr/en : catalogues + Accept-Language + locale persistée)
- [x] Optimisation continue coûts LLM (cache TTL des complétions + métriques coût/tokens)
- [x] Observabilité : /metrics Prometheus + tracing X-Request-ID + Sentry optionnel (Grafana via infra/monitoring)

---

## 3. Structure de dépôt recommandée (monorepo)

```
quantum-trade-ai/
├── README.md
├── docker-compose.yml
├── .github/workflows/          # CI/CD
├── docs/
│   ├── PLAN_COMPLET.md         # ce document
│   ├── architecture.md
│   └── legal/                  # CGU, disclaimers, RGPD
├── backend/                    # FastAPI (Python)
│   ├── app/
│   │   ├── api/                # routes (auth, signals, billing...)
│   │   ├── agents/             # M2 — LangGraph + LiteLLM
│   │   │   ├── master.py
│   │   │   ├── technical.py
│   │   │   ├── sentiment.py
│   │   │   ├── pattern.py
│   │   │   ├── fundamental.py
│   │   │   ├── macro.py
│   │   │   ├── risk.py          # déterministe, pas de LLM
│   │   │   └── journal.py
│   │   ├── data/               # M1 — ingestion, connecteurs WS
│   │   ├── signal_engine/      # M3
│   │   ├── risk/               # M4 — calculs déterministes
│   │   ├── backtest/           # M6
│   │   ├── alerts/             # M7
│   │   ├── execution/          # M8
│   │   ├── billing/            # M10 — Stripe
│   │   ├── core/               # config, security, multi-tenant
│   │   └── models/             # SQLAlchemy / Pydantic
│   └── tests/
├── frontend/                   # Next.js web
│   ├── app/
│   ├── components/             # SignalCard, Chart, Dashboard...
│   └── lib/
├── mobile/                     # React Native (Phase 3)
└── infra/                      # K8s manifests, Terraform
```

---

## 4. Équipe & rôles (rappel)

| Rôle | Nb | Phases clés |
|------|-----|-------------|
| Chef de projet / Product | 1 | Toutes |
| Ingénieur IA / ML | 2 | P1-P3 (agents) |
| Dev backend | 2 | P1-P4 |
| Dev frontend | 2 | P1, P3 (mobile) |
| Designer UI/UX | 1 | P0, P3 |
| Expert finance / quant | 1 | P1-P2 (validation signaux) |
| DevOps | 1 | P0-P5 |

---

## 5. Indicateurs de succès (KPI à instrumenter dès P1)

- **Produit** : précision des signaux (win-rate vérifié), score de confiance vs résultat réel
- **Business** : MRR, conversion free→payant, churn, CAC, LTV, NPS
- **Technique** : latence pipeline, uptime, coût LLM par signal, taux de failover

---

## 6. Risques majeurs & mitigation

| Risque | Niveau | Mitigation |
|--------|--------|-----------|
| Réglementaire | 🔴 Élevé | Avis juridique P0, positionnement « outil » |
| Fiabilité signaux | 🔴 Élevé | Backtesting strict, transparence, score de confiance |
| Confiance utilisateur | 🔴 Élevé | Explicabilité IA, track record vérifié |
| Coût data/LLM | 🟠 Moyen | Routing LiteLLM, plans payants, cache |
| Latence | 🟠 Moyen | Redis, Kafka, infra scalable K8s |
| Concurrence | 🟠 Moyen | Différenciation multi-agents explicable |

---

## 7. Prochaines actions immédiates (semaine 1)

1. [ ] Lancer la consultation juridique (bloquant, délai long)
2. [ ] Initialiser le monorepo + Docker Compose + CI
3. [ ] Ouvrir les comptes API (Anthropic, Binance, Stripe, cloud)
4. [ ] Démarrer les maquettes Figma (Signal Card + Dashboard)
5. [ ] Écrire le schéma de base de données (users, tenants, signals, ohlcv, news)
6. [ ] POC technique : ingestion Binance WS → stockage TimescaleDB → affichage 1 chart

---

## ⚠️ Rappel de fiabilité (à inscrire dans le produit et le marketing)

> Aucun système ne garantit des prédictions exactes — les marchés sont incertains par nature.
> La fiabilité repose sur : **transparence** (score de confiance affiché), **gestion stricte du risque**, **backtesting rigoureux**, et l'avertissement systématique que *les performances passées ne préjugent pas des résultats futurs*.
> **La plateforme fournit une aide à la décision, jamais un conseil en investissement garanti.**

---

*Document généré comme plan d'exécution du cahier des charges Quantum Trade AI v1.0. À maintenir à jour à chaque fin de phase.*

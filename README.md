# Quantum Trade AI

Plateforme SaaS de trading augmentée par une équipe d'agents IA experts.
Voir le plan d'exécution complet : [docs/PLAN_COMPLET.md](docs/PLAN_COMPLET.md).

> ⚠️ **Aide à la décision, pas un conseil en investissement.** Le trading comporte un risque élevé de perte en capital. Les performances passées ne préjugent pas des résultats futurs.

---

## Stack

| Couche | Techno |
|--------|--------|
| Frontend web | Next.js + React + TailwindCSS |
| Backend API | FastAPI (Python 3.11+) |
| Agents IA | LangGraph + LiteLLM (Claude / Gemini) |
| Base de données | PostgreSQL + TimescaleDB |
| Cache / pub-sub | Redis |
| File de messages | Kafka (Redpanda en dev) |
| Infra | Docker + Kubernetes |

## Organisation du dépôt (monorepo)

```
quantum-trade-ai/
├── backend/      # API FastAPI + agents IA + signal/risk engines
├── frontend/     # App web Next.js
├── mobile/       # App React Native (Phase 3)
├── infra/        # docker-compose, init DB, K8s, Terraform
├── docs/         # Plan, architecture, design system, légal
└── .github/      # CI/CD
```

## Démarrage rapide (dev local)

Prérequis : **Docker Desktop** (seul prérequis pour la voie scriptée).

### Le plus simple — un script lance tout

```powershell
# Windows (PowerShell)
.\start.ps1            # build + démarre tout, attend le backend, affiche les URLs
.\start.ps1 -Logs      # idem puis suit les logs
.\stop.ps1             # arrête (  -Purge  pour reset la base )
```

```bash
# Linux / macOS / Git Bash
./start.sh             # build + démarre tout
./start.sh --logs      # idem puis suit les logs
./stop.sh              # arrête (  --purge  pour reset la base )
```

### Ou manuellement avec docker compose

```bash
# 1. Copier les variables d'environnement (le script le fait automatiquement)
cp .env.example .env          # puis renseigner les clés API (optionnel en dev)

# 2. Lancer toute la stack (postgres + redis + redpanda + backend + frontend)
docker compose -f infra/docker-compose.yml up --build

# 3. Vérifier
# Backend  : http://localhost:8090/health  -> {"status":"ok"}
# API docs : http://localhost:8090/docs
# Frontend : http://localhost:3000
```

> **Ports** : le backend est exposé sur **8090** (et non 8000/8080, souvent occupés) et Postgres/Redis/Redpanda
> ne sont **pas** exposés sur l'hôte — ils communiquent en interne via le réseau Docker.
> Cela évite tout conflit si vous avez déjà un Postgres (5432), un Redis (6379) ou un service
> sur 8000 en cours d'exécution. Le backend tourne avec `USE_IN_MEMORY_DB=false` → persistance
> dans le Postgres du compose (volume `pgdata`).
>
> Pour exposer Postgres sur l'hôte (debug), décommentez le mapping `5433:5432` dans
> `infra/docker-compose.yml`.

### Développement sans Docker

```bash
# Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Qualité du code

```bash
# Python
cd backend && ruff check . && black --check . && pytest

# JS/TS
cd frontend && npm run lint && npm run build
```

Les hooks `pre-commit` lancent ruff/black/eslint/prettier automatiquement (`pip install pre-commit && pre-commit install`).

## Environnements

| Env | Usage |
|-----|-------|
| `dev` | Local (docker-compose) |
| `staging` | Pré-production, tests d'intégration |
| `prod` | Production |

## Licence & conformité

Voir [docs/legal/](docs/legal/) (CGU, confidentialité, avertissement risque, RGPD).

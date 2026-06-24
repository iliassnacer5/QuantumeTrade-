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

Prérequis : **Docker Desktop**, **Node 20+ / pnpm 9+**, **Python 3.11+**.

```bash
# 1. Copier les variables d'environnement
cp .env.example .env          # puis renseigner les clés API

# 2. Lancer toute la stack (db + redis + kafka + backend + frontend)
docker compose -f infra/docker-compose.yml up --build

# 3. Vérifier
# Backend  : http://localhost:8000/health  -> {"status":"ok"}
# API docs : http://localhost:8000/docs
# Frontend : http://localhost:3000
```

### Développement sans Docker

```bash
# Backend
cd backend
python -m venv .venv && . .venv/Scripts/activate   # Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload

# Frontend
cd frontend
pnpm install
pnpm dev
```

## Qualité du code

```bash
# Python
cd backend && ruff check . && black --check . && pytest

# JS/TS
cd frontend && pnpm lint && pnpm build
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

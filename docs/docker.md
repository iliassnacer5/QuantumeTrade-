# Dockerisation — Quantum Trade AI

Toute la stack est dockerisée et démarre en une commande.

```bash
docker compose -f infra/docker-compose.yml up --build
```

| Service | Image | Port hôte | Rôle |
|---------|-------|-----------|------|
| backend | build `backend/` | **8090** → 8000 | API FastAPI + agents |
| frontend | build `frontend/` | **3000** | Dashboard Next.js |
| postgres | timescale/timescaledb pg16 | _interne_ | Persistance (volume `pgdata`) |
| redis | redis:7 | _interne_ | Cache / pub-sub |
| redpanda | redpandadata/redpanda | _interne_ | Pipeline (Kafka-compatible) |

**Vérification :** `http://localhost:8090/health` · `http://localhost:8090/docs` · `http://localhost:3000`

## Choix de ports (éviter les conflits)
- Le backend est sur **8090** (8000 et 8080 sont fréquemment occupés, ex. ChromaDB sur 8000, Keycloak sur 8080). Surchargeable via `BACKEND_PORT` dans `.env`.
- Postgres / Redis / Redpanda **ne sont pas exposés** sur l'hôte : ils communiquent par le réseau
  Docker interne (`postgres:5432`, `redis:6379`, `redpanda:9092`). Aucun conflit avec un Postgres
  (5432) ou un Redis (6379) déjà lancés sur votre machine.
- Le frontend reçoit `NEXT_PUBLIC_API_URL=http://localhost:8090` au build (Next.js inline ces
  variables dans le bundle client).

## Persistance
Le backend tourne avec `USE_IN_MEMORY_DB=false` → toutes les données (users, tenants, signals)
sont écrites dans le Postgres du compose. Les tables relationnelles sont créées par l'ORM
(SQLAlchemy `create_all`) au démarrage ; `infra/db/init.sql` ne gère que les hypertables
TimescaleDB (`ohlcv`, `news`). Le volume `pgdata` conserve les données entre redémarrages.

```bash
# Inspecter les données
docker compose -f infra/docker-compose.yml exec postgres psql -U quantum -d quantum -c "\dt"
docker compose -f infra/docker-compose.yml exec postgres psql -U quantum -d quantum -c "SELECT count(*) FROM signals;"
```

## Option : utiliser VOTRE Postgres existant (au lieu de celui du compose)

Si vous avez déjà un conteneur Postgres en cours d'exécution et souhaitez l'utiliser :

1. Créez-y une base et un rôle (ex. base `quantum`, user `quantum`).
2. Dans `infra/docker-compose.yml`, **supprimez** le service `postgres` et son `depends_on` dans
   `backend`, puis pointez le backend vers votre instance via `DATABASE_URL`.

Selon l'emplacement de votre Postgres :
- **Postgres tournant sur l'hôte ou dans un autre conteneur exposé sur l'hôte (5432)** :
  ```yaml
  backend:
    environment:
      USE_IN_MEMORY_DB: "false"
      DATABASE_URL: postgresql+asyncpg://USER:PWD@host.docker.internal:5432/quantum
    extra_hosts:
      - "host.docker.internal:host-gateway"   # nécessaire sous Linux
  ```
- **Postgres dans un autre réseau Docker** : attachez le backend à ce réseau (clé `networks`)
  et utilisez le nom du service Postgres comme hôte.

> Le code convertit automatiquement une URL `postgresql+asyncpg://` en driver synchrone
> (`psycopg2`) pour les repositories SQL — aucune autre modification nécessaire.

> ⚠️ Le schéma TimescaleDB (`ohlcv`/`news`) suppose l'extension `timescaledb`. Sur un Postgres
> standard sans cette extension, les tables relationnelles de l'app fonctionnent quand même
> (l'ORM ne dépend pas de TimescaleDB) ; seules les hypertables de séries temporelles ne seront
> pas créées tant que l'extension n'est pas installée.

## Commandes utiles
```bash
make up        # = docker compose -f infra/docker-compose.yml up --build
make down      # arrêt
make logs      # logs
docker compose -f infra/docker-compose.yml down -v   # arrêt + purge du volume (reset DB)
```

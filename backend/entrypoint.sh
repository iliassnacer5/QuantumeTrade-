#!/usr/bin/env sh
# Entrypoint backend : applique les migrations Alembic puis démarre l'API.
set -e

if [ "${USE_IN_MEMORY_DB:-true}" = "false" ]; then
  echo "==> Application des migrations Alembic (alembic upgrade head)"
  alembic upgrade head || echo "WARN: migrations échouées (poursuite)"
fi

echo "==> Démarrage de l'API"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

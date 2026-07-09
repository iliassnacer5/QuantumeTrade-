#!/usr/bin/env bash
# Lance toute la stack Quantum Trade AI (backend + frontend + postgres + redis + redpanda).
# Usage : ./start.sh [--logs] [--no-build]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE="$ROOT/infra/docker-compose.yml"
FOLLOW_LOGS=0
BUILD="--build"

for arg in "$@"; do
  case "$arg" in
    --logs) FOLLOW_LOGS=1 ;;
    --no-build) BUILD="" ;;
    *) echo "Option inconnue: $arg" ; exit 1 ;;
  esac
done

echo "==> Quantum Trade AI - demarrage"

# 0. Docker disponible ?
if ! docker info >/dev/null 2>&1; then
  echo "ERREUR: Docker ne repond pas. Lancez Docker puis reessayez." >&2
  exit 1
fi

# 1. .env
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  echo "==> .env cree depuis .env.example"
fi

# 2. Build + up
echo "==> docker compose up -d $BUILD"
# shellcheck disable=SC2086
docker compose -f "$COMPOSE" up -d $BUILD

# 3. Attente du backend
BACKEND_PORT="${BACKEND_PORT:-8090}"
printf "==> Attente du backend (http://localhost:%s/health)..." "$BACKEND_PORT"
ready=0
for _ in $(seq 1 40); do
  if [ "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:$BACKEND_PORT/health" 2>/dev/null || echo 000)" = "200" ]; then
    ready=1; break
  fi
  sleep 2; printf "."
done
echo

if [ "$ready" = "1" ]; then
  cat <<EOF

  Stack prete !
  ------------------------------------------
  Dashboard  : http://localhost:3000
  API        : http://localhost:$BACKEND_PORT
  API docs   : http://localhost:$BACKEND_PORT/docs
  ------------------------------------------
  Arret : ./stop.sh   |   Logs : ./start.sh --logs

EOF
else
  echo "  Le backend n'a pas repondu a temps. Voir : docker compose -f infra/docker-compose.yml logs backend"
fi

# 4. Logs optionnels
if [ "$FOLLOW_LOGS" = "1" ]; then
  echo "==> Logs (Ctrl+C pour quitter, la stack reste active)"
  docker compose -f "$COMPOSE" logs -f
fi

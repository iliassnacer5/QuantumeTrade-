#!/usr/bin/env bash
# Arrete la stack Quantum Trade AI. Usage : ./stop.sh [--purge]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE="$ROOT/infra/docker-compose.yml"

if [ "${1:-}" = "--purge" ]; then
  echo "==> Arret + purge du volume Postgres"
  docker compose -f "$COMPOSE" down -v
else
  echo "==> Arret de la stack (donnees conservees)"
  docker compose -f "$COMPOSE" down
fi
echo "==> Stack arretee."

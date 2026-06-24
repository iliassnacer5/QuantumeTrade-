# Quantum Trade AI — commandes de développement
COMPOSE = docker compose -f infra/docker-compose.yml

.PHONY: help up down logs build backend-shell test lint fmt

help:
	@echo "up            - lance toute la stack (docker compose)"
	@echo "down          - arrete la stack"
	@echo "logs          - suit les logs"
	@echo "build         - rebuild les images"
	@echo "test          - lance les tests backend + frontend"
	@echo "lint          - lint backend + frontend"
	@echo "fmt           - formate le code"

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

build:
	$(COMPOSE) build

backend-shell:
	$(COMPOSE) exec backend bash

test:
	cd backend && pytest
	cd frontend && pnpm test --if-present

lint:
	cd backend && ruff check . && black --check .
	cd frontend && pnpm lint

fmt:
	cd backend && ruff check --fix . && black .
	cd frontend && pnpm exec prettier --write .

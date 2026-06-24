# Observabilité — Phase 5

## Métriques (Prometheus / Grafana)
L'API expose `GET /metrics` au format d'exposition Prometheus (sans dépendance native).

Métriques clés :
- `http_requests_total{method,route,status}` — trafic HTTP
- `http_request_duration_seconds{method,route}` — histogramme de latence (p50/p95/p99)
- `signals_generated_total{direction}` — signaux produits
- `orders_placed_total{mode,side}` — ordres (papier/réel)
- `llm_calls_total{provider,role}` / `llm_errors_total` — usage LLM
- `llm_cache_hits_total{role}` — efficacité du cache (réduction des coûts)
- `llm_cost_usd_total{provider}` / `llm_tokens_total{provider}` — coût estimé

### Lancer Prometheus en local
```bash
docker run -p 9090:9090 -v "$PWD/infra/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml" prom/prometheus
```
Puis brancher Grafana sur la source Prometheus (`http://localhost:9090`).

## Santé / SLA
- `GET /health/live` — liveness (uptime). Sonde Kubernetes `livenessProbe`.
- `GET /health/ready` — readiness : vérifie la base (et Redis). Renvoie 503 si dégradé. Sonde `readinessProbe`.

## Tracing
Chaque requête reçoit un `X-Request-ID` (généré ou propagé). Les logs d'accès incluent
`method route status durée rid=<request-id>` pour la corrélation.

## Sentry (erreurs)
Optionnel : définir `SENTRY_DSN` dans `.env` active la capture d'erreurs (no-op si vide).
Nécessite `pip install sentry-sdk` (non inclus par défaut).

# Comptes & accès fournisseurs (Phase 0.4)

Liste des comptes à ouvrir et des clés à renseigner dans `.env` (voir `.env.example`).

| Service | Variable(s) `.env` | Usage | Phase | Statut |
|---------|--------------------|-------|-------|--------|
| **Anthropic (Claude)** | `ANTHROPIC_API_KEY` | Raisonnement, Master Agent, Copilot | MVP | ⬜ |
| **Google (Gemini)** | `GOOGLE_API_KEY` | Volume, vision, grounding | P2 | ⬜ |
| **Binance** | `BINANCE_API_KEY`, `BINANCE_API_SECRET` | Données crypto OHLCV/order book | MVP | ⬜ |
| **Finnhub** | `FINNHUB_API_KEY` | News / sentiment | MVP | ⬜ |
| **NewsAPI** | `NEWSAPI_KEY` | Actualités | MVP | ⬜ |
| **Stripe** | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_STARTER` | Facturation | MVP | ⬜ |
| **Telegram** | `TELEGRAM_BOT_TOKEN` | Alertes push | MVP | ⬜ |
| **Resend / SendGrid** | `RESEND_API_KEY` | Alertes email | MVP | ⬜ |
| **Cloud (AWS/GCP)** | _(infra)_ | Déploiement + registry Docker | P0/P1 | ⬜ |

## Gestion des secrets

- **Dev** : fichier `.env` local (jamais committé — protégé par `.gitignore`).
- **Staging / prod** : Vault / AWS Secrets Manager / Doppler. Jamais de secret en clair dans le code ou la CI.
- Rotation régulière des clés. Clés broker (Phase 4) : **chiffrées et révocables**, jamais d'accès aux fonds.

## Notes par fournisseur

- **Binance** : pour le MVP, des clés en lecture seule suffisent (pas de trading avant Phase 4). Penser aux limites de rate.
- **LiteLLM** : route vers Anthropic/Google selon l'agent ; configurer le failover dès le MVP même si un seul fournisseur est actif.
- **Stripe** : configurer les webhooks (`checkout.session.completed`, `customer.subscription.*`) vers `/api/billing/webhook`.

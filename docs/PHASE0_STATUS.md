# Phase 0 — État d'avancement

Statut des tâches du cahier des charges. ✅ = livré dans ce dépôt · 🟡 = scaffold/brouillon prêt, action humaine requise · ⬜ = à faire (hors code).

## 0.1 — Juridique & conformité
| Tâche | Statut | Note |
|-------|--------|------|
| Consulter un avocat (AMF/SEC/FCA) | ⬜ | Action humaine — BLOQUANT avant lancement |
| Statut réglementaire (outil vs conseil) | 🟡 | Brouillons + checklist dans `docs/legal/` |
| CGU, confidentialité, non-responsabilité | 🟡 | Brouillons rédigés, à valider juridiquement |
| Avertissement risque affiché partout | ✅ | `docs/legal/disclaimer.md` + intégré UI (page d'accueil) |
| Cadrage RGPD | 🟡 | `docs/legal/rgpd.md` (registre + checklist) |
| Anticiper KYC/AML (Phase 4) | ✅ | Documenté |

## 0.2 — Setup technique du dépôt
| Tâche | Statut | Note |
|-------|--------|------|
| Monorepo (pnpm/turbo + backend Python) | ✅ | `package.json`, `pnpm-workspace.yaml`, `turbo.json` |
| Git + branches + conventions commit | ✅ | Dépôt initialisé, voir README |
| CI/CD (GitHub Actions) | ✅ | `.github/workflows/ci.yml` (lint+test+docker) |
| Environnements dev/staging/prod | ✅ | `.env.example` + `ENVIRONMENT` |
| Gestion des secrets | ✅ | `.env` gitignored, doc Vault/Doppler |
| Docker Compose dev local | ✅ | `infra/docker-compose.yml` |
| Linters/formatters | ✅ | ruff+black (Py), eslint+prettier (JS) |
| Pre-commit hooks | ✅ | `.pre-commit-config.yaml` |

## 0.3 — Design & maquettes
| Tâche | Statut | Note |
|-------|--------|------|
| Wireframes 9 écrans | ✅ | `docs/screens-wireframes.md` |
| Design system (dark, couleurs, typo) | ✅ | `docs/design-system.md` + `tailwind.config.ts` |
| Maquettes Figma haute-fidélité | 🟡 | Specs prêtes ; SignalCard implémentée en code ; Figma = action humaine |
| États temps réel spécifiés | ✅ | `docs/design-system.md` |

## 0.4 — Comptes & accès fournisseurs
| Tâche | Statut | Note |
|-------|--------|------|
| Clés Anthropic + Google | 🟡 | Slots dans `.env.example` — à renseigner |
| Binance (+ backup) | 🟡 | Slots prêts |
| Finnhub + NewsAPI | 🟡 | Slots prêts |
| Stripe | 🟡 | Slots prêts |
| Cloud + registry Docker | ⬜ | Action humaine (compte AWS/GCP) |
| Telegram + email | 🟡 | Slots prêts |

Voir `docs/accounts-setup.md`.

## 🧪 Definition of Done Phase 0
| Critère | Statut |
|---------|--------|
| `docker compose up` lance toute la stack | ✅ Configuré (`infra/docker-compose.yml`) |
| Endpoint `/health` répond | ✅ Implémenté + testé (`pytest` vert, 4/4) |
| Maquettes validées | 🟡 Specs + design system prêts ; validation Figma humaine |
| Cadre juridique documenté | ✅ Brouillons + checklists ; validation avocat = humain |

## Reste strictement humain (hors périmètre code)
1. Rendez-vous avocat droit financier (lancer en J1)
2. Ouverture des comptes fournisseurs + saisie des clés dans `.env`
3. Production des maquettes Figma haute-fidélité
4. Création des comptes cloud (AWS/GCP) + provisioning

## Prochaine étape : Phase 1 (MVP)
Démarrer par le POC : ingestion Binance WS → TimescaleDB → 1 chart, puis Agent Technique + Sentiment → Signal Engine → SignalCard live.

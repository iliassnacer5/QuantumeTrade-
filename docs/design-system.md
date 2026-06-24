# Design System — Quantum Trade AI

## Principes (cf. cahier des charges §5.1)

- **Dark mode par défaut** — adapté aux longues sessions de trading.
- **Lisibilité instantanée des signaux** — code couleur BUY/SELL sans ambiguïté.
- **Mobile-first** pour les alertes en mobilité.
- **Latence perçue minimale** — mises à jour temps réel sans rechargement.

## Palette de couleurs (tokens Tailwind)

| Token | Hex | Usage |
|-------|-----|-------|
| `background` | `#0B0E11` | Fond global |
| `surface` | `#151A21` | Cartes, panneaux |
| `border` | `#232A33` | Séparateurs, contours |
| `muted` | `#8A94A6` | Texte secondaire |
| `buy` / `accent` | `#1D9E75` | Direction BUY, succès, vert |
| `sell` | `#E24B4A` | Direction SELL, risque, rouge |
| `buy-soft` / `sell-soft` | `…22` | Fonds de badges (alpha 13%) |

> Les accents officiels du cahier des charges sont **rouge `#E24B4A`** et **vert `#1D9E75`**.

## Typographie

- **Sans** : Inter (UI générale)
- **Mono** : JetBrains Mono (prix, chiffres, niveaux — alignement et lisibilité)

## Composants clés

- **SignalCard** — unité d'information centrale (`frontend/components/SignalCard.tsx`). Champs : actif, direction (badge coloré), entrée, SL, TP1/2/3, R/R, barre de confiance, justification IA, timeframe.
- **Chart** — TradingView Lightweight Charts avec annotations IA (Phase 1).
- **Heatmap marché**, **Watchlist**, **P&L** — Dashboard (Phase 1).

## États temps réel à spécifier

| État | Comportement |
|------|--------------|
| `loading` | Skeleton shimmer, pas de saut de layout |
| `live update` | Transition douce, flash subtil sur changement de prix |
| `stale` | Badge « données en retard » si flux WS interrompu |
| `error/flux` | Bandeau de reconnexion + dernière valeur connue grisée |

## Maquettes Figma (à produire en Phase 0)

Wireframes des 9 écrans (cf. [screens-wireframes.md](screens-wireframes.md)) + maquettes haute-fidélité de la **Signal Card** et du **Dashboard**. Lien Figma : _à compléter_.

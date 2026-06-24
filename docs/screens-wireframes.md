# Wireframes — 9 écrans clés

Spécification textuelle des écrans (cf. cahier des charges §5.2). Sert de base aux maquettes Figma.

## 1. Onboarding
Profil de risque (conservative / moderate / aggressive), objectifs, marchés suivis. Capital de départ, tolérance au risque par trade (%).

## 2. Dashboard
Signaux live (liste de SignalCards, WebSocket), watchlist, P&L global, heatmap marché. Zone principale = flux de signaux ; latérale = watchlist + résumé portefeuille.

## 3. Signal Card (écran détail)
Tous les champs du signal + graphique miniature + justification IA détaillée + bouton « voir sur le chart » / « créer une alerte ».

```
┌─────────────────────────────┐
│ BTC/USDT            [ BUY ] │
│ Entrée 64 250  SL 62 800    │
│ TP 66 000 / 68 500 / 71 000 │
│ R/R 1:3.2   ███████░░ 82%   │
│ Justif IA : cassure + ...   │
│ Swing (H4)                  │
└─────────────────────────────┘
```

## 4. Graphique
Chart interactif (TradingView Lightweight Charts) avec annotations IA, niveaux clés (entrée/SL/TP), overlays d'indicateurs.

## 5. Portefeuille
Positions ouvertes, exposition par actif/secteur, performance, drawdown courant, alertes de surexposition.

## 6. Backtesting
Configuration de stratégie (actif, timeframe, période, règles) + résultats : equity curve, Sharpe, win-rate, max DD, profit factor.

## 7. Journal
Historique des trades + explication IA + analyse des erreurs + tags / leçons.

## 8. AI Copilot
Chat conversationnel pour interroger un actif (« Que penses-tu de l'ETH aujourd'hui ? »). Réponses streamées avec contexte marché + sorties d'agents.

## 9. Paramètres
Alertes (canaux, seuils), connexions broker (Phase 4), abonnement & facturation, MFA / sécurité.

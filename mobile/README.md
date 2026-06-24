# Quantum Trade AI — App mobile (Expo / React Native)

App iOS + Android qui **réutilise le même backend FastAPI** que le web (Phase 3.1). Pensée
mobile-first pour les alertes en mobilité (notifications push natives).

## Écrans
- **Login / Register** — authentification JWT (token persisté via AsyncStorage).
- **Signaux** — liste live des signaux, génération à la demande, pull-to-refresh.
- **AI Copilot** — chat contextuel (variante non-stream, robuste sur réseau mobile). Réservé Pro.

## Notifications push
Au lancement, l'app demande la permission et récupère un **Expo push token**, transmis au backend
via `PATCH /api/settings` (`push_token`). Le backend l'utilise dans `notify_signal` → `send_push`
pour pousser les nouveaux signaux.

## Démarrer
```bash
cd mobile
npm install
npm start          # puis 'a' (Android), 'i' (iOS) ou QR code Expo Go
```

## Configuration
L'URL de l'API est dans `app.json` → `expo.extra.apiUrl` (défaut `http://localhost:8080`).
Sur appareil physique, remplace `localhost` par l'IP LAN de la machine qui héberge le backend.

## Réutilisation de la logique
`src/api.ts` reflète `frontend/lib/api.ts` (mêmes endpoints, même contrat). Les types `Signal`/`Me`
sont alignés sur les schémas backend.

## Build stores (suite)
`eas build` (Expo Application Services) pour générer les binaires iOS/Android et publier. Nécessite
un compte Expo + identifiants Apple/Google (hors périmètre code).

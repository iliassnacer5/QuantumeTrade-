# PLAN FRONTEND 2026 — Refonte UI/UX complète

> Audit du frontend actuel + plan d'implémentation pour une interface fluide, professionnelle,
> niveau « produit fintech 2026 » : design system, navigation repensée, micro-animations, 3D ciblée,
> zéro redondance. Sans casser les fonctionnalités existantes (tout est branché sur la même API).

---

## 1. AUDIT DE L'EXISTANT (mesuré)

**23 pages** · **5 composants seulement** · aucune lib d'animation · aucune lib de primitives UI.

| Problème mesuré | Ampleur | Impact |
|---|---|---|
| Navbar horizontale à **18 liens** | 1 barre qui déborde | Navigation illisible, pas de hiérarchie |
| Header « Titre + ← Dashboard » copié-collé | **14 pages** | Incohérences, poids mort |
| Sélecteur de marché (Crypto/Forex/Actions/Or) dupliqué | **5 pages** | 5 versions à maintenir |
| Sélecteur de sessions dupliqué | 4 pages | idem |
| Carte `rounded-xl border bg-surface` ad hoc | **40 occurrences** | Aucun composant Card |
| Gestion d'erreur 402 (plan) copiée-collée | 6 pages | UX d'upgrade incohérente |
| Pages monolithiques | execution 410 lignes, dashboard 335 | Difficile à faire évoluer |
| Pas de skeletons/toasts/empty-states unifiés | partout | « Chargement… » texte brut |
| Pas d'animations | 0 transition | Sensation statique, pas 2026 |
| Landing/login sans identité | basiques | Première impression faible |

**Points forts à garder** : palette dark sobre (fond #0B0E11, buy/sell vert/rouge), Tailwind bien
utilisé, lightweight-charts pour les graphes, structure App Router propre, i18n partiel.

---

## 2. CIBLE — les principes « 2026 »

1. **App shell : sidebar + topbar** (fini la navbar 18 liens) : sidebar groupée par intention —
   *Trader* (Ma journée, Dashboard, Scanner, Trades du jour) · *Prouver* (Edge, Stratégies, Backtest,
   Track record) · *Exécuter* (Paper trading, Portefeuille, Journal) · *Plus* (Copilot, Agents,
   Marketplace, Réglages). Topbar : recherche symbole, mode de sévérité, statut données ● LIVE, user.
2. **Design tokens complets** : échelle typographique, espacements, rayons, ombres, élévations,
   gradients de marque (vert→cyan), variantes de cartes (default / glass / elevated / danger).
3. **Micro-interactions partout (Framer Motion)** : transitions de pages (fade+slide 150 ms),
   listes en stagger, compteurs animés (equity, P&L), hover lift sur cartes, feedback boutons.
4. **3D ciblée et performante** (pas de gadget global) :
   - **Landing + Login** : fond WebGL réactif (vagues de particules façon « flux de marché »,
     react-three-fiber, lazy-loadé, fallback statique) — l'effet « wow » au premier contact.
   - **Cartes/valeurs clés** : tilt 3D subtil au survol (CSS transform, 0 coût bundle).
   - PAS de 3D sur les pages de travail (dashboard/scanner) : la donnée prime, 60 fps garanti.
5. **États soignés** : skeletons (shimmer) pour chaque fetch, empty-states illustrés avec action,
   toasts (succès/erreur) via `sonner`, erreurs 402 → un seul composant `UpgradeGate` élégant.
6. **Raccourcis pro** : palette de commandes **Ctrl+K** (aller à une page, chercher un symbole,
   générer un signal), navigation clavier.
7. **Responsive réel** : sidebar → bottom-nav mobile (5 entrées), tableaux → cartes empilées.
8. **Accessibilité** : contrastes AA, focus visibles, aria sur les contrôles, prefers-reduced-motion.

---

## 3. NOUVELLE BIBLIOTHÈQUE DE COMPOSANTS (`components/ui/` + `components/domain/`)

**Primitives (ui/)** — remplacent les 40+ blocs ad hoc :
`Button` (variants primary/ghost/danger/buy/sell) · `Card` (default/glass/stat) · `Badge` ·
`Stat` (valeur + delta animé) · `Tabs` · `Select` · `Segmented` (boutons groupés) · `Table`
(tri, sticky header, scroll-x) · `Skeleton` · `EmptyState` · `Modal` · `Tooltip` · `Toast` ·
`ProgressBar` · `PageHeader` (titre, sous-titre, actions).

**Métier (domain/)** — factorisent les duplications mesurées :
`MarketSelector` (Tous/Crypto/Forex/Actions/Or — 5 pages) · `SessionPicker` (4 pages) ·
`SymbolPicker` (recherche + catalogue) · `TimeframePicker` · `DirectionBadge` (BUY/SELL/HOLD) ·
`EdgeStatusDot` (🟢🟡🔴) · `OutcomeBanner` (gagné/perdu/en cours) · `UpgradeGate` (402) ·
`DataSourceBadge` (live/réel/démo) · `AgentScoreBar` · `RiskDisclaimer`.

**Dépendances ajoutées (léger, justifié)** :
`framer-motion` (animations) · `sonner` (toasts) · `cmdk` (Ctrl+K) · `lucide-react` (icônes
cohérentes) · `@react-three/fiber` + `three` (landing/login uniquement, en dynamic import).

---

## 4. PLAN D'IMPLÉMENTATION (5 phases, ~6-8 sessions)

### Phase F1 — Fondations (1 session)
- Tokens Tailwind étendus (typographie, ombres, gradients, animations keyframes).
- Primitives `ui/` (Button, Card, Badge, Stat, PageHeader, Skeleton, EmptyState, Table, Segmented).
- **App shell** : `Sidebar` groupée + `Topbar` + layout responsive ; suppression NavBar 18 liens.
- Framer Motion : template de transition de page + stagger util.
- Toasts `sonner` branchés sur les erreurs API globales.
- ✅ Critère : toutes les pages rendent dans le nouveau shell sans régression fonctionnelle.

### Phase F2 — Composants métier + dé-duplication (1 session)
- `MarketSelector`, `SessionPicker`, `SymbolPicker`, `TimeframePicker`, `DirectionBadge`,
  `UpgradeGate`, `DataSourceBadge`, `OutcomeBanner`, `EdgeStatusDot`, `AgentScoreBar`.
- Remplacement dans les 14 pages : headers → `PageHeader`, sélecteurs → composants partagés,
  56+ blocs dupliqués supprimés.
- ✅ Critère : `grep "id: 'crypto', label"` → 1 seule occurrence ; ~-500 lignes de code.

### Phase F3 — Refonte des pages cœur (2 sessions)
Ordre = valeur pour le trader :
1. **☀️ Ma journée** : hero « brief du matin » avec stats animées, régime en carte glass, top
   opportunités en carrousel de cartes.
2. **Dashboard** : grille modulaire (chart central, ticker live, signaux récents en stagger),
   génération de signal avec état de progression par agent (les 8 agents « s'allument »).
3. **🗺️ Edge** : matrice heatmap interactive (au lieu du tableau), tri/filtres, sparkline de
   stabilité par combo.
4. **Scanner** : table pro (tri, virtualisation si >50 lignes), ligne extensible → mini-analyse.
5. **Prédiction /signal/[id]** : timeline visuelle de la décision (données → agents → pesée →
   gates → verdict), jauges contexte/timing, pesée du Master en barres animées.

### Phase F4 — Pages d'exécution & le reste (1-2 sessions)
6. **Paper trading** : ticket d'ordre en drawer latéral (plus de prompt()), positions en cartes
   avec P&L latent animé, clôture avec confirmation modale.
7. **Portefeuille** : courbe d'équité en aire dégradée, stats en `Stat` animés.
8. **Stratégies / Backtest / Track record** : tabs unifiés, résultats en cartes comparables.
9. **Journal / Copilot / Réglages / Plans** : alignement sur les primitives ; Copilot en vraie
   interface de chat (bulles, streaming avec curseur, suggestions en chips).

### Phase F5 — Wow & polish (1 session)
- **Landing + Login 3D** : fond particules WebGL (flux de marché) lazy-loadé + hero copy pro +
  fallback image statique (mobile/reduced-motion).
- **Ctrl+K** : navigation + recherche symbole + actions rapides.
- Compteurs animés sur toutes les valeurs monétaires ; tilt 3D sur cartes stats.
- Audit final : responsive mobile (bottom-nav), a11y (focus, contrastes), Lighthouse ≥ 90 perf.

---

## 5. GARDE-FOUS
- **Zéro régression fonctionnelle** : mêmes appels API, mêmes flux ; refonte = présentation.
- **Perf d'abord** : 3D uniquement landing/login en `next/dynamic` (`ssr:false`) ; bundle des pages
  de travail inchangé ; `prefers-reduced-motion` respecté partout.
- **Incremental** : chaque phase livre un état déployable (`docker compose up --build frontend`).
- **Typecheck + build à chaque phase** ; smoke test des 23 pages (HTTP 200 + rendu).

## 6. ORDRE DE DÉMARRAGE RECOMMANDÉ
F1 (fondations + shell) est le prérequis de tout : c'est lui qui fait passer l'app de « site à
18 onglets » à « produit pro ». Démarrer là.

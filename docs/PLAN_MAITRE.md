# PLAN MAÎTRE A→Z — Rendre Quantum Trade AI « gagnante »

> Analyse complète du projet (agents, stratégies, métriques, backtest) + feuille de route
> d'implémentation de A à Z. Fondé sur les résultats MESURÉS de la plateforme, pas sur des promesses.
>
> **Règle d'or** : personne — humain ou IA — ne peut garantir des prédictions gagnantes. Ce plan
> définit « gagnant » de façon mesurable, maximise les chances d'y arriver, et garantit surtout que
> tu SAURAS si tu y es (ou pas) avant de risquer de l'argent réel.

---

## 0. DÉFINITION OPÉRATIONNELLE DE « GAGNANT »

Une combinaison (stratégie/moteur × marché × timeframe × mode) est déclarée **gagnante** si :
1. **Alpha > 0** vs buy & hold, **après frais** (0,15 %/côté), en walk-forward out-of-sample ;
2. **Profit factor ≥ 1,2** régulier sur les folds (pas un fold chanceux) ;
3. **Confirmé en forward test** : ≥ 4 semaines de trading auto papier avec PF ≥ 1,1 réel.

Tout le plan vise à produire, prouver et exploiter de telles combinaisons — et à s'abstenir partout ailleurs.

---

## 1. ÉTAT DES LIEUX MESURÉ (juillet 2026)

### 1.1 Ce que la plateforme sait déjà faire (acquis, ~197 tests verts)
- **8+1 agents** : technical (routeur → 4 experts marché), volume, sentiment, pattern, fundamental,
  macro, risk, master (arbitrage pondéré + bonus expert ×1,3 + anti-dilution), journal (apprentissage
  par marché, bayésien n/(n+12)).
- **4 marchés** : crypto (Binance live WS), actions (Alpaca réel), forex (Yahoo, OANDA prêt),
  **or/métaux** (COMEX via Yahoo) — avec un agent expert dédié par marché.
- **8 stratégies** déterministes backtestables + comparateur + validation multi-symboles.
- **Backtest honnête** : frais+slippage, benchmark buy&hold, alpha, walk-forward, A/B des sorties.
- **Gates de fiabilité** : multi-timeframe 2/3, qualité (confiance/ADX/R-R), anti-couteau (EMA longue),
  blackout événementiel (earnings/FOMC), modes strict/équilibré/agressif.
- **Boucle complète** : signal → prédiction consultable (pesée du Master, 14 figures, pivots, Fibonacci,
  news scorées par titre) → trade papier (auto ou manuel) → issue réelle → apprentissage par marché →
  track record + « trades évités ».
- **Infra** : 100 % dockerisée, migrations auto, GitHub, déployable partout (guide Oracle inclus).

### 1.2 Les chiffres qui comptent (mesurés sur la plateforme elle-même)
| Mesure | Résultat | Enseignement |
|---|---|---|
| A/B sorties (12 comparaisons) | **tp_only gagne 12/12** | breakeven/trailing tronquaient les gagnants → défaut corrigé |
| Anti-couteau (filtre EMA longue) | win rate 26,9 % → **40 %** | ne jamais trader contre la tendance de fond |
| **MTF EMA × 4h × tp_only** | **PF 1,14 · alpha +10,4 %** (BTC+ETH+SOL, OOS) | seul combo positif après frais à ce jour |
| Tout en 1h | PF 0,25–0,71, alpha négatif | le 1h est trop bruité : à éviter |
| 1d | PF 1,09 mais alpha −38 % | rentable mais sous le buy&hold : inutile |
| Journal réel (41 trades, tests) | 22 % win, P&L −164 | pas d'edge sur les vieux réglages ; base à assainir |

### 1.3 Diagnostic critique par composant
| Composant | Force | Limite actuelle |
|---|---|---|
| Agents experts | Règles métier réelles (DXY, funding, SPX, taux réels) | Funding géo-bloqué ; pas d'open interest ni d'order flow |
| Master | Pondération apprise + anti-dilution | N'apprend pas encore À REFUSER ses propres signaux (méta-filtrage) |
| Stratégies | 8 familles couvrant tendance/retour/cassure/volume | Une seule combo prouvée positive ; pas de carte d'edge systématique |
| Backtest | Honnête (frais, alpha, OOS) | TP fixe 2,5×ATR jamais optimisé OOS ; sizing fixe 1 % |
| Données | 3 sources réelles + live crypto | Indicateurs classiques = connus de tous = peu d'edge par définition |
| Apprentissage | Par marché, pondéré volume | Peu de données propres (base polluée par les tests) |

**Le verdict honnête** : la MACHINE est excellente (mesure, discipline, transparence — meilleure que
la plupart des humains sur ces points). L'EDGE, lui, n'est prouvé que sur UNE combinaison. Le but du
plan : industrialiser la découverte d'edge et ne trader que là où il est prouvé.

---

## 2. LE PLAN A→Z (7 phases, ordonnées)

### PHASE A — Hygiène de mesure — ✅ OUTILLÉE (reste 3 clics côté utilisateur)
Le thermomètre doit être propre avant de soigner.
- [x] Outillage : `DELETE /api/journal` (reset journal) + reset Portefeuille existant.
- [ ] **À toi (2 min)** : 💰 Portefeuille → Réinitialiser ; Journal → reset ; Stratégies → choisir
      `mtf_ema` + activer 🤖 Trading auto papier ; Dashboard → mode ⚖️ Équilibré.
- [x] Alertes/auto-trade alignés sur le **4h** (le timeframe validé) — configurable.
- **Critère de sortie** : baseline propre qui accumule des trades réels simulés 24/7.

### PHASE B — La CARTE DE L'EDGE — ✅ IMPLÉMENTÉE (juil. 2026)
Arrêter de chercher l'edge à la main : le systématiser.
- [x] **Sweep nocturne** (`edge_sweep_loop`, 24 h, 1er passage ~10 min après boot) : walk-forward de
      8 stratégies × 18 symboles (4 marchés) × {4h, 1d}, bougies chargées 1 fois par symbole×TF.
- [x] **Page 🗺️ /edge** : matrice 🟢/🟡/🔴 par marché, tri par alpha, filtre par statut, colonne
      **Stabilité** (sweeps verts consécutifs), bouton « Relancer le sweep ».
- [x] **Règle d'or automatisée** : l'auto-trading papier ne prend QUE les combos 🟢
      (`auto_trade_green_only`, streak minimal configurable `edge_min_green_streak`).
- **Critère de sortie** : liste vivante et auto-mise-à-jour des combos exploitables. ✅

### PHASE C — DONNÉES À AVANTAGE (1 semaine, dépend du VPS)
Les indicateurs RSI/MACD sont dans tous les manuels : l'edge durable vient de données moins exploitées.
- [ ] **VPS (Oracle Always Free, guide prêt)** → débloque `fapi.binance.com` : funding réel, **open
      interest**, ratio long/short → nouveaux inputs de l'expert crypto.
- [ ] **Order flow simplifié** : delta volume acheteur/vendeur par bougie (Binance aggTrades) →
      nouvel input volume/crypto_expert.
- [ ] **OANDA** (clé à créer) → forex réel avec vrais spreads.
- [ ] **Calendrier éco complet** : NFP/CPI/BCE en plus du FOMC (fenêtres configurées, pas de scraping fragile).
- **Critère de sortie** : chaque nouvel input passe par la Phase B — s'il n'améliore pas l'alpha OOS, il dégage.

### PHASE D — LE CERVEAU (méta-intelligence, 3-4 jours)
Rendre le Master capable de refuser ses propres signaux — c'est ce qui sépare un pro d'un débutant.
- [ ] **Régime au niveau moteur** : ADX journalier décide quelles familles de stratégies/agents ont
      le droit de voter (tendance vs range) — généralisation du regime_router à tout le pipeline.
- [ ] **Méta-filtrage (meta-labeling)** : avec ≥100 trades journalisés, entraîner un filtre simple
      (logistique sur : consensus, ADX, contexte_score, timing_score, régime, marché) qui prédit
      « ce signal a-t-il historiquement gagné ? » → nouveau gate optionnel, validé OOS comme le reste.
- [ ] **Bascule d'apprentissage** : quand un agent a n≥30 par marché, son multiplicateur passe de
      [0,5-1,5] à [0,3-1,7] (plus incisif quand les données le justifient).
- **Critère de sortie** : le méta-filtre améliore le PF OOS d'au moins +0,1 vs sans filtre — sinon il n'entre pas en prod.

### PHASE E — EXÉCUTION & RISQUE PRO (2 jours)
Un edge modeste survit ou meurt selon l'exécution et le sizing.
- [ ] **Sizing adaptatif** : fraction de Kelly cappée à 1,5 % (f = win_rate − (1−win_rate)/RR, ÷4,
      plancher 0,25 %) alimenté par le win rate RÉEL du journal par combo.
- [ ] **Stop de perte quotidien** : −3 % du capital papier/jour → gel des entrées jusqu'au lendemain.
- [ ] **A/B du TP** (2 / 2,5 / 3 / 4 ×ATR) via l'endpoint exit-ab existant, OOS multi-symboles —
      on garde le meilleur, on n'itère pas plus (anti-overfitting).
- [ ] **Filtre horaire** : pas d'entrée crypto pendant les heures de liquidité morte (03-06 UTC) si
      la mesure du slippage le justifie.
- **Critère de sortie** : drawdown max OOS réduit sans détruire l'alpha.

### PHASE F — FORWARD TEST DISCIPLINÉ (4-8 semaines, incompressible)
Le juge de paix. Aucun raccourci possible.
- [ ] Auto-trading papier sur les combos verts uniquement, sizing Phase E.
- [ ] Revue hebdomadaire : Portefeuille (PF réel, win réel) vs prédiction du backtest.
- [ ] **Go/No-Go final** : PF forward ≥ 1,1 sur ≥ 40 trades → seulement alors envisager du réel
      (petit, avec l'avis juridique fait). Sinon : retour Phase B/C avec les enseignements.

### PHASE G — PRODUCTION & LÉGAL (en parallèle de F)
- [ ] VPS + HTTPS (Caddy) + backups Postgres + monitoring (le /metrics existe déjà).
- [ ] Telegram (token à créer : 2 min) → alertes + digest sur téléphone.
- [ ] **Avis juridique** (statut éditeur d'outils vs conseil, AMF/MiFID, CGU) — obligatoire avant
      tout utilisateur tiers payant. Rien ne remplace un avocat.

---

## 3. « MEILLEURS QUE LES EXPERTS HUMAINS » — CE QUI EST VRAI ET CE QUI NE L'EST PAS

**Là où tes agents battent DÉJÀ un humain expert** :
- Couverture : 80+ symboles × 4 marchés analysés en continu — aucun humain ne fait ça.
- Discipline : les gates s'appliquent à 100 % des cas, jamais de fatigue, de FOMO ou de revenge trading.
- Transparence : chaque décision est auditable au chiffre près (pesée, poids, contributions).
- Mémoire : l'apprentissage par marché n'oublie jamais un trade et ne se raconte pas d'histoires.

**Là où AUCUN système (ni humain) n'a de garantie** :
- Prédire la direction du marché. Les meilleurs fonds quantitatifs du monde gagnent avec des PF de
  1,1-1,3 et des années de R&D. Un PF de 1,14 mesuré honnêtement est déjà un résultat sérieux.

**La conclusion pratique** : ne cherche pas l'agent-oracle. Cherche un système qui trade PEU, seulement
là où l'edge est prouvé, avec un sizing qui survit aux séries perdantes — c'est exactement ce que
construit ce plan, et c'est déjà plus que ce que fait 95 % des traders humains.

---

## 4. RISQUES & ANTI-PATTERNS (à relire avant chaque itération)
1. **Overfitting** : chaque idée se valide OOS multi-symboles ou n'existe pas. Max 1 A/B par levier.
2. **Cherry-picking de période** : la carte de l'edge doit montrer la stabilité TEMPORELLE des combos.
3. **Pollution du thermomètre** : ne plus jamais mélanger trades de test et track record (Phase A).
4. **Chiffres promis** : aucun objectif de win rate n'est promis à un utilisateur — on affiche le mesuré.
5. **Réel prématuré** : pas d'argent réel avant le Go de la Phase F + légal fait.

## 5. ORDRE D'EXÉCUTION RÉSUMÉ
```
A (½ j, toi+moi) → B (2-3 j, moi) → C (1 sem, VPS+clés toi / code moi)
      → D (3-4 j, moi) → E (2 j, moi) → F (4-8 sem, le temps) → G (parallèle)
```
Prochaine action immédiate : **Phase A** (reset + config de référence + auto-trade ON) puis je code la
**Phase B (carte de l'edge)** — c'est elle qui transforme « j'espère gagner » en « je sais où je gagne ».

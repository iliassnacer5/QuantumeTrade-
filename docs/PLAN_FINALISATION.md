# PLAN DE FINALISATION — Quantum Trade AI

> État mesuré, ce qui manque pour des prédictions fiables, et feuille de route pour finaliser.
> Règle d'honnêteté : personne ne peut GARANTIR des prédictions « gagnantes ». Ce plan maximise
> les chances d'en trouver et donne les outils pour le PROUVER — ou pour savoir s'abstenir.

---

## 1. ÉTAT MESURÉ (juillet 2026, BTC 1h, frais 0,15%/côté inclus)

| Moteur / stratégie | Win rate | PF | Alpha vs buy&hold |
|---|---|---|---|
| Moteur multi-agents (anti-couteau actif) | 40,0% | 0,25 | −9,8% |
| Volume Profile / VWAP | 40,0% | 0,36 | −17,9% |
| Ichimoku | 40,5% | 0,26 | −18,6% |
| MTF EMA | 38,8% | 0,32 | −20,5% |
| SMC / Order Blocks | 27,3% | 0,27 | −11,9% |

**Verdict honnête : aucun edge prouvé.** L'infrastructure est complète et honnête, mais les
prédictions actuelles PERDENT de l'argent après frais sur cette période.

**Diagnostic précis (mesuré, pas deviné)** :
1. ✅ Le filtre anti-couteau a fonctionné : win rate 26,9% → 40%.
2. 🔴 Le problème restant : **les gains sont tronqués**. Le breakeven verrouille +0,3R dès +1R ;
   les gagnants sortent à ~0,3-0,5R pendant que les pertes restent à 1R pleine.
   Math : 0,40×0,4R gagné vs 0,60×1R perdu → PF ≈ 0,27. Il faut un gain moyen ≥ 1,5R pour être
   rentable à 40% de réussite.
3. 🔴 Période de test courte (~40 jours de 1h) et marché baissier/haché — défavorable aux
   stratégies de tendance, et trop court pour conclure.

---

## 2. CE QU'IL FAUT POUR DES PRÉDICTIONS FIABLES

### A. Corrections mesurables immédiates (code, 1-2 jours)
1. **Laisser courir les gagnants** : A/B test au walk-forward —
   (a) breakeven/trailing OFF, TP 2,5×ATR seul ; (b) breakeven à +1,5R au lieu de +1R ;
   (c) TP étagé (moitié à 1,5R, reste en trailing). Garder LA config qui maximise l'expectancy
   out-of-sample. C'est le levier n°1 identifié par les maths ci-dessus.
2. **Valider sur le journalier (1d) et 4h** : plus d'historique (des années), moins de bruit,
   frais moins pénalisants (moins de trades). Les stratégies de tendance y marchent mieux.
3. **Filtre de régime** : ne trader les stratégies tendance QUE quand le marché tend
   (ADX journalier > 25) ; sinon Z-score seulement. Router la stratégie selon le régime.

### B. Recherche d'alpha (itératif, semaines — sans garantie)
4. **Données à avantage** : funding rates réels (débloquer fapi hors géo-restriction ou via un
   proxy), open interest, ratio long/short Binance, on-chain (exchanges inflows). Les indicateurs
   classiques (RSI/MACD) sont connus de tous → peu d'edge par définition.
5. **Sélection de marché** : le comparateur multi-symboles doit tourner sur 15-20 paires × 3
   timeframes ; ne trader QUE les combinaisons où l'alpha out-of-sample est positif et régulier.
6. **Forward test = juge final** : 2-3 mois de paper trading automatique (stratégie active +
   alertes + clôture auto) → le Portefeuille virtuel et le Journal donnent le VRAI win rate.
   Aucun backtest ne remplace ça.

### C. Complétude produit (dépend de tes clés/comptes)
7. **Clés Alpaca (paper)** → vraies données actions + ordres paper Alpaca réels.
8. **Clé OANDA** → forex réel (sinon Yahoo, sans volume).
9. **Stripe + Telegram** si monétisation/alertes réelles.

### D. Production & légal (avant tout usage par des tiers)
10. Secret JWT fort, session 60 min en prod, HTTPS, backups Postgres.
11. **Avis juridique** : statut « éditeur d'outils » vs conseiller (AMF/MiFID), CGU, disclaimers.
    Rien ne remplace un avocat. Risque n°1 du projet si distribué.

---

## 3. FEUILLE DE ROUTE (ordre d'exécution)

### Semaine 1 — Le levier stops + régime — ✅ FAIT ET MESURÉ (juil. 2026)
- [x] A/B test des sorties (4 configs × BTC/ETH/SOL × 1h/4h/1d, walk-forward, frais inclus)
      → **`tp_only` gagne 12/12 comparaisons** (SL/TP fixes, sans breakeven ni trailing).
      Le diagnostic était juste : breakeven+trailing tronquaient les gagnants (config `current`
      dernière partout, PF 0,37-0,62). **Nouvelle config par défaut appliquée.**
- [x] Validation 1d/4h → **le 4h est le meilleur timeframe** :
      | Combo | Alpha | PF |
      |---|---|---|
      | **MTF EMA × 4h × tp_only** | **+10,4%** | **1,14** ✅ premier combo positif après frais |
      | regime_router × 4h | +8,9% | 0,93 |
      | ichimoku × 4h | +8,2% | 0,83 |
      | mtf_ema × 1h | −4,6% | 0,71 |
      | mtf_ema × 1d | −38% (buy&hold très fort sur 3 ans) | 1,09 (rentable mais sous le hold) |
- [x] Filtre de régime : stratégie `regime_router` ajoutée (ADX>25→MTF EMA ; ADX<20→Z-score).
- Critère de succès (alpha>0, PF>1,2) : **presque atteint** (PF 1,14). Nuance honnête : une seule
  période, 3 symboles — c'est le forward test qui confirmera.

### Semaines 2-4 — Forward test en continu — ✅ OUTILLÉ, EN COURS
- [x] **Trading auto papier** : toggle 🤖 sur la page Stratégies — chaque signal de la stratégie
      active ouvre automatiquement un trade papier (1% risque, SL/TP, clôture auto).
      → Recommandation : stratégie active = `mtf_ema`, timeframe 4h, auto ON, puis lire le
      💰 Portefeuille chaque semaine.
- [ ] Lecture hebdo du Portefeuille virtuel / Journal (win rate réel, PF réel) — à toi de jouer
- [x] L'apprentissage par marché affine les poids pendant ce temps

### En parallèle
- [x] Alpaca paper branché (données actions réelles vérifiées, bug `start` corrigé)
- [ ] OANDA (forex réel) — en attente de ta clé
- [ ] Funding rates — en attente d'un environnement non géo-bloqué

### Avant toute mise en production publique
- [x] Warning au démarrage si SECRET_KEY par défaut ; session 60 min documentée (.env.example)
- [ ] HTTPS + backups Postgres — au moment du déploiement
- [ ] Consultation juridique — hors code, incompressible

---

## 4. CE QUE CE PLAN NE PROMET PAS

Un logiciel ne rend pas le marché prévisible. Ce plan livre :
- un produit **fini** techniquement (déjà ~95% fait, ~166 tests verts),
- une machine à **mesurer** l'edge honnêtement (walk-forward + frais + benchmark + forward test),
- les meilleures pratiques pour en **trouver** un (sorties, régime, timeframes, sélection de marché).

Si après ces étapes aucune combinaison ne montre d'alpha positif régulier, la conclusion honnête
sera : ne pas trader ces signaux en réel — et c'est précisément la valeur du système : il te
l'aura dit AVANT que tu perdes de l'argent.

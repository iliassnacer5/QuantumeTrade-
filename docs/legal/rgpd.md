# Cadrage RGPD — checklist

> Brouillon de cadrage. Validation par DPO / juriste requise.

## Registre des traitements (à tenir)
| Traitement | Finalité | Base légale | Données | Conservation |
|------------|----------|-------------|---------|--------------|
| Gestion des comptes | Fournir le service | Contrat | Email, nom, mdp haché | Vie du compte + X |
| Profil trading | Personnalisation | Contrat | Profil de risque, watchlists | Vie du compte |
| Facturation | Paiement | Contrat / obligation légale | Données Stripe | Durée légale comptable |
| Journalisation trades | Service + apprentissage | Intérêt légitime | Trades, P&L | Vie du compte |
| Logs techniques | Sécurité | Intérêt légitime | IP, sessions | Durée limitée |
| Marketing | Communication | Consentement | Email | Jusqu'au retrait |

## Mesures à mettre en place
- [ ] Registre des traitements documenté
- [ ] Désigner un DPO si traitement à grande échelle / suivi régulier
- [ ] Procédure d'exercice des droits (accès, effacement, portabilité…)
- [ ] Bandeau cookies + gestion du consentement
- [ ] DPA (accords de sous-traitance) avec hébergeur, Stripe, fournisseurs LLM
- [ ] Encadrement des transferts hors UE (CCT)
- [ ] Politique de minimisation des données envoyées aux LLM
- [ ] Procédure de notification de violation (72h)
- [ ] Analyse d'impact (AIPD) si traitement à risque

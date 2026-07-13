Chaque agent est spécialisé sur une classe d'actifs ou un domaine d'analyse :

| Agent | Domaine | Rôle |
|-------|---------|------|
| ₿ **Crypto Agent** | Cryptomonnaies | Analyse et signaux sur le marché crypto |
| 💱 **Forex Agent** | Devises | Analyse des paires de devises |
| 📊 **Stocks Agent** | Actions | Analyse des marchés actions |
| 🌍 **Macro Agent** | Contexte économique | Filtrage via calendrier économique et régime de marché |

L'**orchestrateur** collecte les signaux des agents, applique un scoring de consensus et détecte le régime de marché avant de produire une recommandation.

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| 🎯 **Signaux de consensus** | Agrégation pondérée des signaux de plusieurs agents |
| 📉 **Détection de régime de marché** | Identification des phases (tendance, range, volatilité) |
| ⏮️ **Backtesting** | Test des stratégies sur données historiques |
| 📅 **Filtrage économique** | Prise en compte du calendrier économique |
| ⚡ **Temps réel** | Traitement continu via infrastructure scalable |

---

## 🛠️ Stack technique

**Backend / IA** — Python · FastAPI · LangGraph (orchestration multi-agents)
**Frontend** — Next.js · React
**Data & Infra** — TimescaleDB (séries temporelles) · Redis (cache temps réel)
**Architecture** — Système multi-agents (agents spécialisés, consensus, orchestration)

---

## 📸 Aperçu

<!-- Ajoute tes captures ici :
![Dashboard](./screenshots/dashboard.png)
-->
*Captures d'écran à venir.*

---

## ⚠️ Avertissement

Ce projet est développé à des fins éducatives et de recherche. Il ne constitue pas un conseil en investissement. Le trading comporte des risques de perte en capital.

---

<p align="center"><i>Quantum Trade AI — Plusieurs agents, une décision éclairée.</i></p>

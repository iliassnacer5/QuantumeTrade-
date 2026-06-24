"""M2 — Couche d'agents IA (LangGraph + LiteLLM).

Agents prévus :
- master.py       : orchestration & arbitrage (Claude Sonnet)
- technical.py    : indicateurs déterministes + résumé LLM
- sentiment.py    : NLP news / social
- pattern.py      : figures chartistes (vision, Gemini) — Phase 2
- fundamental.py  : santé de l'actif — Phase 2
- macro.py        : contexte macro (grounding) — Phase 2
- risk.py         : contraintes risque (déterministe, PAS de LLM)
- journal.py      : mémoire & apprentissage — Phase 3

Implémenté à partir de la Phase 1 (Technique + Sentiment + Master).
"""

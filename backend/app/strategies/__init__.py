"""Bibliothèque de stratégies de trading classiques, déterministes et backtestables."""

from app.strategies.library import REGISTRY, get_strategy, list_strategies

__all__ = ["REGISTRY", "get_strategy", "list_strategies"]

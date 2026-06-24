"""Internationalisation (Phase 5) — catalogues de traduction + résolution de locale.

Catalogues fr/en servis au frontend via /api/i18n/{locale}. La locale effective est déterminée par
la préférence utilisateur puis l'en-tête Accept-Language, avec repli sur le français.
"""

from __future__ import annotations

DEFAULT_LOCALE = "fr"
SUPPORTED = ("fr", "en")

CATALOG: dict[str, dict[str, str]] = {
    "fr": {
        "app.name": "Quantum Trade AI",
        "nav.dashboard": "Tableau de bord",
        "nav.signals": "Signaux",
        "nav.copilot": "Copilot IA",
        "nav.journal": "Journal",
        "nav.backtest": "Backtest",
        "nav.execution": "Exécution",
        "nav.copytrading": "Copy-trading",
        "nav.marketplace": "Marketplace",
        "nav.plans": "Abonnement",
        "nav.settings": "Paramètres",
        "signal.buy": "Achat",
        "signal.sell": "Vente",
        "signal.hold": "Attente",
        "common.upgrade": "Mettre à niveau",
        "common.logout": "Déconnexion",
        "disclaimer": "Aide à la décision, pas un conseil en investissement.",
    },
    "en": {
        "app.name": "Quantum Trade AI",
        "nav.dashboard": "Dashboard",
        "nav.signals": "Signals",
        "nav.copilot": "AI Copilot",
        "nav.journal": "Journal",
        "nav.backtest": "Backtest",
        "nav.execution": "Execution",
        "nav.copytrading": "Copy-trading",
        "nav.marketplace": "Marketplace",
        "nav.plans": "Subscription",
        "nav.settings": "Settings",
        "signal.buy": "Buy",
        "signal.sell": "Sell",
        "signal.hold": "Hold",
        "common.upgrade": "Upgrade",
        "common.logout": "Log out",
        "disclaimer": "Decision support, not investment advice.",
    },
}


def normalize(locale: str | None) -> str:
    if not locale:
        return DEFAULT_LOCALE
    code = locale.split(",")[0].split("-")[0].strip().lower()
    return code if code in SUPPORTED else DEFAULT_LOCALE


def resolve(user_locale: str | None, accept_language: str | None) -> str:
    """Locale effective : préférence utilisateur > Accept-Language > défaut."""
    if user_locale and user_locale in SUPPORTED:
        return user_locale
    return normalize(accept_language)


def t(key: str, locale: str | None = None) -> str:
    loc = normalize(locale)
    return CATALOG.get(loc, CATALOG[DEFAULT_LOCALE]).get(key, key)


def catalog(locale: str | None) -> dict[str, str]:
    return CATALOG.get(normalize(locale), CATALOG[DEFAULT_LOCALE])

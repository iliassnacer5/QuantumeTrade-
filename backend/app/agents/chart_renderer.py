"""Rendu de graphique (chandeliers) en base64 pour l'agent Vision."""

from __future__ import annotations

import base64
import io

import matplotlib
import matplotlib.pyplot as plt

# Désactiver l'interface graphique
matplotlib.use("Agg")

from app.domain.indicators import Candle


def render_chart_base64(candles: list[Candle], symbol: str = "Symbol", timeframe: str = "TF") -> str:
    """Génère un graphique en chandeliers et retourne l'image en base64."""
    if not candles:
        return ""

    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Préparer les données. On utilise des indices entiers pour l'axe X : les bougies live n'ont
    # pas toujours de timestamp (None), ce qui rendait l'axe en dtype object et cassait ax.bar().
    times = list(range(len(candles)))
    opens = [c.open for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    closes = [c.close for c in candles]

    # Couleurs
    up_color = "green"
    down_color = "red"

    # Dessiner les chandeliers
    for i in range(len(candles)):
        color = up_color if closes[i] >= opens[i] else down_color
        # Mèche (High-Low)
        ax.plot([times[i], times[i]], [lows[i], highs[i]], color=color, linewidth=1)
        # Corps (Open-Close)
        # On utilise une barre avec bottom = min(O,C) et height = |O-C|
        bottom = min(opens[i], closes[i])
        height = max(abs(closes[i] - opens[i]), 1e-5) # Éviter hauteur 0
        ax.bar(times[i], height, bottom=bottom, color=color, width=0.8, align="center")

    ax.set_title(f"{symbol} - {timeframe}")
    ax.set_xlabel("Bougies (récentes à droite)")
    ax.grid(True, linestyle=":", alpha=0.6)

    # Sauvegarde en mémoire
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

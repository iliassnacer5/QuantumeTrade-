"""Génération et export de rapports de backtest."""

from __future__ import annotations

import json
from pathlib import Path

from app.backtest.schemas import BacktestReport


def export_report_to_json(report: BacktestReport, output_dir: str = "reports") -> str:
    """Exporte un rapport de backtest en fichier JSON et retourne le chemin."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    
    filename = f"backtest_{report.config.symbol.replace('/', '_')}_{report.id[:8]}.json"
    filepath = path / filename
    
    # Custom encoder for datetime
    def default_serializer(obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
        
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, default=default_serializer, indent=2)
        
    return str(filepath)

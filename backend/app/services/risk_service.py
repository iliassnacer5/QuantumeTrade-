"""Application des règles de protection du capital (Lot 2).

Calcule l'état de risque d'un utilisateur (exposition, signaux du jour) et applique des garde-fous
au moment de la génération : exposition maximale, nombre de signaux quotidien, alerte drawdown.
Déterministe — aucun LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.models.entities import User
from app.repositories.store import AppStore


def _is_today(iso_or_dt) -> bool:
    if iso_or_dt is None:
        return False
    if isinstance(iso_or_dt, str):
        try:
            dt = datetime.fromisoformat(iso_or_dt)
        except ValueError:
            return False
    else:
        dt = iso_or_dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).date() == datetime.now(UTC).date()


@dataclass
class RiskStatus:
    capital: float
    exposure_value: float
    exposure_pct: float
    max_exposure_pct: float
    daily_signals: int
    max_daily_signals: int
    breaches: list[str]

    def as_dict(self) -> dict:
        return {
            "capital": round(self.capital, 2),
            "exposure_value": round(self.exposure_value, 2),
            "exposure_pct": round(self.exposure_pct, 2),
            "max_exposure_pct": self.max_exposure_pct,
            "daily_signals": self.daily_signals,
            "max_daily_signals": self.max_daily_signals,
            "breaches": self.breaches,
            "ok": not self.breaches,
        }


def compute_status(user: User, store: AppStore) -> RiskStatus:
    signals = store.signals.list_for_tenant(user.tenant_id, limit=500)
    today = [s for s in signals if _is_today(s.payload.get("created_at") or s.created_at)]
    exposure_value = sum(
        float(s.payload.get("position_value") or 0)
        for s in today
        if s.payload.get("direction") in ("BUY", "SELL")
    )
    exposure_pct = (exposure_value / user.capital * 100) if user.capital > 0 else 0.0
    daily_signals = len(today)

    breaches: list[str] = []
    if exposure_pct > user.max_exposure_pct:
        breaches.append(
            f"Exposition {exposure_pct:.0f}% > plafond {user.max_exposure_pct:.0f}%"
        )
    if daily_signals >= user.max_daily_signals:
        breaches.append(f"Limite de {user.max_daily_signals} signaux/jour atteinte")

    return RiskStatus(
        capital=user.capital,
        exposure_value=exposure_value,
        exposure_pct=exposure_pct,
        max_exposure_pct=user.max_exposure_pct,
        daily_signals=daily_signals,
        max_daily_signals=user.max_daily_signals,
        breaches=breaches,
    )


def check_can_generate(user: User, store: AppStore) -> tuple[bool, str | None]:
    """Autorise ou non une nouvelle génération. (ok, raison_si_bloque).

    Générer un signal = produire une ANALYSE, pas ouvrir une position : on ne bloque donc PAS sur
    l'exposition (qui devient un simple avertissement sur la carte). On conserve uniquement une
    limite de débit quotidienne anti-abus (coûts API/LLM).
    """
    status = compute_status(user, store)
    if status.daily_signals >= user.max_daily_signals:
        return False, f"Limite quotidienne de {user.max_daily_signals} analyses atteinte."
    return True, None


def real_exposure_pct(user: User, store: AppStore) -> float:
    """Exposition issue des ordres RÉELLEMENT exécutés (papier/réel), pas des analyses générées.

    Utilisée par l'Agent Risque pour ne pénaliser la confiance qu'en présence de vraies positions :
    générer une analyse ne doit pas dégrader la qualité des signaux suivants.
    """
    try:
        orders = store.records.list("order", user.tenant_id)
    except Exception:  # noqa: BLE001 — pas de store records (mode dégradé)
        return 0.0
    notional = sum(float(o.get("filled_price") or 0) * float(o.get("qty") or 0) for o in orders)
    return (notional / user.capital * 100) if user.capital > 0 else 0.0


def generation_warning(user: User, store: AppStore) -> str | None:
    """Avertissement de risque (non bloquant) à afficher sur la carte signal."""
    status = compute_status(user, store)
    if status.exposure_pct >= user.max_exposure_pct:
        return (
            f"⚠️ Exposition simulée {status.exposure_pct:.0f}% ≥ plafond {user.max_exposure_pct:.0f}%. "
            f"Prudence avant d'ouvrir une nouvelle position."
        )
    return None

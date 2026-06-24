"""Copy-trading (Phase 4) — suivi des top traders + copie auto avec garde-fous.

Collections (store.records) :
- trader_profile : profil PUBLIC opt-in d'un trader (stats dérivées du journal). Confidentialité :
  un trader n'apparaît au classement que s'il publie son profil.
- copy_follow    : relation suiveur -> leader + contrôles de risque (allocation, plafond, seuil).
- commission     : partage de revenus crédité au leader à chaque copie.

Garde-fous de copie : allocation en % du capital du suiveur, plafond par trade, seuil de confiance,
et exécution en **papier** (aucune clé broker requise pour copier).
"""

from __future__ import annotations

import uuid

from app.execution.paper import PaperBroker
from app.repositories.store import AppStore
from app.services import journal_service

PROFILE = "trader_profile"
FOLLOW = "copy_follow"
COMMISSION = "commission"

COMMISSION_RATE = 0.001  # 0,1 % du notionnel copié, crédité au leader (démo de partage de revenus)


# ---------------- Profils publics / leaderboard ----------------
def publish_profile(store: AppStore, tenant_id: str, display_name: str) -> dict:
    stats = journal_service.stats(journal_service.recent_entries(store, tenant_id, limit=500))
    return store.records.put(
        PROFILE, tenant_id,
        {
            "display_name": display_name or "Trader",
            "win_rate": stats["win_rate"],
            "total_pnl": stats["total_pnl"],
            "closed_trades": stats["closed"],
            "published": True,
        },
        tenant_id=tenant_id,
    )


def unpublish_profile(store: AppStore, tenant_id: str) -> bool:
    return store.records.delete(PROFILE, tenant_id)


def refresh_profile(store: AppStore, tenant_id: str) -> None:
    """Met à jour les stats du profil public s'il existe (après un nouveau trade clôturé)."""
    prof = store.records.get(PROFILE, tenant_id)
    if prof:
        publish_profile(store, tenant_id, prof.get("display_name", "Trader"))


def leaderboard(store: AppStore, limit: int = 50) -> list[dict]:
    profs = store.records.list(PROFILE)
    profs.sort(key=lambda p: (p.get("total_pnl", 0.0), p.get("win_rate", 0.0)), reverse=True)
    return [
        {
            "tenant_id": p["tenant_id"],
            "display_name": p.get("display_name"),
            "win_rate": p.get("win_rate"),
            "total_pnl": p.get("total_pnl"),
            "closed_trades": p.get("closed_trades"),
        }
        for p in profs[:limit]
    ]


# ---------------- Suivi ----------------
def follow(
    store: AppStore, follower_tenant: str, leader_tenant: str,
    *, allocation_pct: float = 5.0, max_per_trade: float = 1000.0, min_confidence: int = 60,
) -> dict:
    if follower_tenant == leader_tenant:
        raise ValueError("impossible de se suivre soi-même")
    if store.records.get(PROFILE, leader_tenant) is None:
        raise ValueError("ce trader n'est pas public")
    follow_id = str(uuid.uuid4())
    return store.records.put(
        FOLLOW, follow_id,
        {
            "leader_tenant": leader_tenant,
            "allocation_pct": max(0.1, min(allocation_pct, 100.0)),
            "max_per_trade": max(1.0, max_per_trade),
            "min_confidence": min_confidence,
            "active": True,
        },
        tenant_id=follower_tenant,
    )


def unfollow(store: AppStore, follower_tenant: str, follow_id: str) -> bool:
    rec = store.records.get(FOLLOW, follow_id)
    if rec is None or rec.get("tenant_id") != follower_tenant:
        return False
    return store.records.delete(FOLLOW, follow_id)


def following(store: AppStore, follower_tenant: str) -> list[dict]:
    return store.records.list(FOLLOW, follower_tenant)


def _followers_of(store: AppStore, leader_tenant: str) -> list[dict]:
    return [f for f in store.records.list(FOLLOW) if f.get("leader_tenant") == leader_tenant and f.get("active")]


def _follower_capital(store: AppStore, follower_tenant: str) -> float:
    users = store.users.list_by_tenant(follower_tenant)
    return users[0].capital if users else 10000.0


# ---------------- Copie automatique ----------------
async def on_leader_signal(store: AppStore, leader_tenant: str, card) -> int:
    """Réplique un signal du leader vers ses suiveurs (papier), avec contrôles de risque.

    Retourne le nombre de copies exécutées. N'a aucun effet si le leader n'est pas public.
    """
    if store.records.get(PROFILE, leader_tenant) is None:
        return 0
    direction = card.direction.value if hasattr(card.direction, "value") else str(card.direction)
    if direction not in {"BUY", "SELL"}:
        return 0
    side = "buy" if direction == "BUY" else "sell"
    entry = float(getattr(card, "entry", 0.0)) or 0.0
    confidence = int(getattr(card, "confidence", 0) or 0)

    broker = PaperBroker(name="copy")
    count = 0
    for f in _followers_of(store, leader_tenant):
        if confidence < int(f.get("min_confidence", 60)):
            continue
        capital = _follower_capital(store, f["tenant_id"])
        budget = min(capital * float(f["allocation_pct"]) / 100.0, float(f["max_per_trade"]))
        if entry <= 0 or budget <= 0:
            continue
        qty = round(budget / entry, 6)
        if qty <= 0:
            continue
        result = await broker.place_order(card.asset, side, qty)
        notional = (result.filled_price or entry) * qty
        # Trace l'ordre copié dans le journal d'ordres du suiveur.
        store.records.put(
            "order", str(uuid.uuid4()),
            {
                "conn_id": None, "broker": "copy", "mode": "paper", "symbol": card.asset,
                "side": side, "qty": qty, "status": result.status,
                "filled_price": result.filled_price, "copied_from": leader_tenant,
            },
            tenant_id=f["tenant_id"],
        )
        # Partage de revenus crédité au leader.
        store.records.put(
            COMMISSION, str(uuid.uuid4()),
            {"follower_tenant": f["tenant_id"], "amount": round(notional * COMMISSION_RATE, 4), "symbol": card.asset},
            tenant_id=leader_tenant,
        )
        count += 1
    return count


def commissions(store: AppStore, leader_tenant: str) -> dict:
    items = store.records.list(COMMISSION, leader_tenant)
    return {"total": round(sum(float(i.get("amount", 0.0)) for i in items), 4), "count": len(items), "items": items[:50]}

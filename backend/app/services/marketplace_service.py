"""Marketplace (Phase 4) — stratégies & agents IA à la vente + clés API dev payantes.

Collections (store.records) :
- listing      : annonce publique (stratégie ou config d'agent) mise en vente.
- purchase     : achat d'une annonce par un acheteur (débloque la config).
- dev_api_key  : clé API développeur/institutionnelle (API payante). Stockée HASHÉE.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid

from app.repositories.store import AppStore

LISTING = "listing"
PURCHASE = "purchase"
API_KEY = "dev_api_key"

_TYPES = {"strategy", "agent"}


# ---------------- Annonces ----------------
def create_listing(
    store: AppStore, seller_tenant: str, *, title: str, kind: str, price: float, description: str, config: dict
) -> dict:
    if kind not in _TYPES:
        raise ValueError("type d'annonce invalide (strategy|agent)")
    listing_id = str(uuid.uuid4())
    return store.records.put(
        LISTING, listing_id,
        {
            "title": title, "kind": kind, "price": max(0.0, price),
            "description": description, "config": config or {},
            "seller_tenant": seller_tenant, "active": True,
        },
        tenant_id=seller_tenant,
    )


def list_listings(store: AppStore) -> list[dict]:
    return [_public_listing(l) for l in store.records.list(LISTING) if l.get("active")]


def _public_listing(l: dict) -> dict:
    # La config n'est révélée qu'après achat.
    return {
        "id": l["id"], "title": l.get("title"), "kind": l.get("kind"),
        "price": l.get("price"), "description": l.get("description"),
        "seller_tenant": l.get("seller_tenant"), "created_at": l.get("created_at"),
    }


def buy_listing(store: AppStore, buyer_tenant: str, listing_id: str) -> dict:
    listing = store.records.get(LISTING, listing_id)
    if listing is None or not listing.get("active"):
        raise ValueError("annonce introuvable")
    if listing.get("seller_tenant") == buyer_tenant:
        raise ValueError("vous êtes le vendeur de cette annonce")
    purchase_id = str(uuid.uuid4())
    store.records.put(
        PURCHASE, purchase_id,
        {"listing_id": listing_id, "title": listing.get("title"), "price": listing.get("price"),
         "seller_tenant": listing.get("seller_tenant"), "config": listing.get("config", {})},
        tenant_id=buyer_tenant,
    )
    # En prod : déclencher le paiement Stripe + le partage de revenus vendeur ici.
    return {"purchase_id": purchase_id, "config": listing.get("config", {})}


def my_purchases(store: AppStore, buyer_tenant: str) -> list[dict]:
    return store.records.list(PURCHASE, buyer_tenant)


# ---------------- Clés API développeur ----------------
def issue_api_key(store: AppStore, tenant_id: str, label: str) -> dict:
    raw = "qta_" + secrets.token_urlsafe(24)
    key_id = str(uuid.uuid4())
    store.records.put(
        API_KEY, key_id,
        {
            "label": label or "default",
            "key_hash": hashlib.sha256(raw.encode()).hexdigest(),
            "prefix": raw[:12],
            "active": True,
        },
        tenant_id=tenant_id,
    )
    # La clé en clair n'est renvoyée qu'une seule fois.
    return {"id": key_id, "api_key": raw, "prefix": raw[:12]}


def list_api_keys(store: AppStore, tenant_id: str) -> list[dict]:
    return [
        {"id": k["id"], "label": k.get("label"), "prefix": k.get("prefix"),
         "active": k.get("active"), "created_at": k.get("created_at")}
        for k in store.records.list(API_KEY, tenant_id)
    ]


def revoke_api_key(store: AppStore, tenant_id: str, key_id: str) -> bool:
    rec = store.records.get(API_KEY, key_id)
    if rec is None or rec.get("tenant_id") != tenant_id:
        return False
    return store.records.delete(API_KEY, key_id)

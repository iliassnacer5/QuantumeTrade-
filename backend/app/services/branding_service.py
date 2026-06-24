"""White-label (Phase 5) — branding par tenant + résolution par domaine personnalisé.

Collections (store.records) :
- branding : configuration de marque d'un tenant (nom, logo, couleur, domaine).
- domain   : index domaine -> tenant_id pour la résolution publique (rendu white-label).
"""

from __future__ import annotations

from app.repositories.store import AppStore

BRANDING = "branding"
DOMAIN = "domain"

_DEFAULT = {
    "brand_name": "Quantum Trade AI",
    "primary_color": "#1D9E75",
    "logo_url": "",
    "custom_domain": "",
}


def get_branding(store: AppStore, tenant_id: str) -> dict:
    rec = store.records.get(BRANDING, tenant_id)
    if rec is None:
        return {**_DEFAULT, "tenant_id": tenant_id}
    return {**_DEFAULT, **{k: rec.get(k) for k in _DEFAULT if rec.get(k) is not None}, "tenant_id": tenant_id}


def set_branding(
    store: AppStore, tenant_id: str, *, brand_name: str | None, primary_color: str | None,
    logo_url: str | None, custom_domain: str | None,
) -> dict:
    current = get_branding(store, tenant_id)
    new = {
        "brand_name": brand_name or current["brand_name"],
        "primary_color": primary_color or current["primary_color"],
        "logo_url": logo_url if logo_url is not None else current["logo_url"],
        "custom_domain": (custom_domain or "").strip().lower(),
    }
    # Réindexe le domaine -> tenant (en supprimant l'ancien s'il a changé).
    old_domain = current.get("custom_domain") or ""
    if old_domain and old_domain != new["custom_domain"]:
        store.records.delete(DOMAIN, old_domain)
    if new["custom_domain"]:
        store.records.put(DOMAIN, new["custom_domain"], {"target_tenant": tenant_id}, tenant_id=tenant_id)
    store.records.put(BRANDING, tenant_id, new, tenant_id=tenant_id)
    return get_branding(store, tenant_id)


def resolve_by_domain(store: AppStore, domain: str) -> dict | None:
    """Résolution publique : branding associé à un domaine personnalisé (white-label)."""
    idx = store.records.get(DOMAIN, (domain or "").strip().lower())
    if idx is None:
        return None
    tenant_id = idx.get("target_tenant")
    b = get_branding(store, tenant_id)
    # Vue publique (pas d'info sensible).
    return {"brand_name": b["brand_name"], "primary_color": b["primary_color"], "logo_url": b["logo_url"]}

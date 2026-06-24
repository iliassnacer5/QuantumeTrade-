'use client';

import { useEffect, useState } from 'react';
import { api, ApiKey, Listing, PlanInfo } from '@/lib/api';

export default function MarketplacePage() {
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [purchases, setPurchases] = useState<any[]>([]);
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [l, p] = await Promise.all([api.listings(), api.purchases()]);
      setListings(l);
      setPurchases(p);
    } catch (e: any) {
      setError(e.message);
    }
  }
  useEffect(() => {
    api.myPlan().then((pl) => {
      setPlan(pl);
      if (pl.features.api_access) api.apiKeys().then(setKeys).catch(() => {});
    }).catch(() => {});
    load();
  }, []);

  const canSell = plan?.features.marketplace_sell;
  const canDev = plan?.features.api_access;

  async function createListing() {
    const title = prompt('Titre de l’annonce ?');
    if (!title) return;
    const kind = prompt('Type (strategy|agent) ?', 'strategy') ?? 'strategy';
    const price = parseFloat(prompt('Prix ($) ?', '49') ?? '0');
    const description = prompt('Description ?') ?? '';
    try {
      await api.createListing({ title, kind, price, description, config: { weights: { technical: 0.5, volume: 0.5 } } });
      load();
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function buy(l: Listing) {
    try {
      await api.buyListing(l.id);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function issueKey() {
    const label = prompt('Label de la clé ?', 'default') ?? 'default';
    const r = await api.createApiKey(label);
    setNewKey(r.api_key);
    api.apiKeys().then(setKeys);
  }

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Marketplace</h1>
          <p className="text-sm text-muted">Stratégies & agents IA · API développeur</p>
        </div>
        <div className="flex gap-2">
          {canSell && <button onClick={createListing} className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">+ Vendre</button>}
          <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">← Dashboard</a>
        </div>
      </header>

      {error && <p className="text-sell">{error}</p>}

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {listings.length === 0 && <p className="text-muted">Aucune annonce.</p>}
        {listings.map((l) => {
          const bought = purchases.find((p) => p.listing_id === l.id);
          return (
            <div key={l.id} className="flex flex-col rounded-xl border border-border bg-surface p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium text-white">{l.title}</h3>
                <span className="rounded bg-muted/20 px-2 py-0.5 text-xs text-muted">{l.kind}</span>
              </div>
              <p className="mt-1 flex-1 text-sm text-gray-400">{l.description}</p>
              <div className="mt-3 flex items-center justify-between">
                <span className="text-lg font-bold text-white">{l.price}$</span>
                {bought ? (
                  <span className="text-xs text-buy">✓ Acheté</span>
                ) : (
                  <button onClick={() => buy(l)} className="rounded bg-accent px-3 py-1 text-xs text-white">Acheter</button>
                )}
              </div>
            </div>
          );
        })}
      </section>

      {canDev && (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Clés API développeur</h2>
            <button onClick={issueKey} className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">+ Générer une clé</button>
          </div>
          {newKey && (
            <div className="rounded-lg border border-accent/40 bg-accent/10 p-3 text-sm text-white">
              Nouvelle clé (copiée une seule fois) : <span className="font-mono break-all">{newKey}</span>
            </div>
          )}
          {keys.map((k) => (
            <div key={k.id} className="flex items-center justify-between rounded-lg border border-border bg-surface p-3 text-sm">
              <span className="text-white">{k.label}</span>
              <span className="font-mono text-muted">{k.prefix}…</span>
              <button onClick={() => api.revokeApiKey(k.id).then(() => api.apiKeys().then(setKeys))} className="text-xs text-sell">Révoquer</button>
            </div>
          ))}
        </section>
      )}
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { api, Branding, PlanInfo } from '@/lib/api';
import { PageHeader } from '@/components/ui';

export default function BrandingPage() {
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [b, setB] = useState<Branding | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    api.myPlan().then(setPlan).catch(() => {});
    api.branding().then(setB).catch(() => {});
  }, []);

  const locked = plan && !plan.features.white_label;

  async function save() {
    if (!b) return;
    setMsg(null);
    try {
      const saved = await api.setBranding(b);
      setB(saved);
      setMsg('Branding enregistré.');
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  if (locked)
    return (
      <div className="p-8">
        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-6 text-yellow-200">
          Le white-label est réservé au plan <b>Enterprise</b>.{' '}
          <a href="/plans" className="underline">Nous contacter</a>
        </div>
      </div>
    );
  if (!b) return <div className="p-8 text-white">Chargement…</div>;

  return (
    <div className="p-8 space-y-6">
      <PageHeader title="White-label" />

      <div className="grid gap-6 md:grid-cols-2">
        <section className="space-y-3 rounded-xl border border-border bg-surface p-5">
          <label className="block text-sm text-muted">Nom de marque
            <input value={b.brand_name} onChange={(e) => setB({ ...b, brand_name: e.target.value })}
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-white" />
          </label>
          <label className="block text-sm text-muted">Couleur principale
            <input type="color" value={b.primary_color} onChange={(e) => setB({ ...b, primary_color: e.target.value })}
              className="mt-1 h-10 w-full rounded-lg border border-border bg-background" />
          </label>
          <label className="block text-sm text-muted">URL du logo
            <input value={b.logo_url} onChange={(e) => setB({ ...b, logo_url: e.target.value })}
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-white" placeholder="https://…" />
          </label>
          <label className="block text-sm text-muted">Domaine personnalisé
            <input value={b.custom_domain ?? ''} onChange={(e) => setB({ ...b, custom_domain: e.target.value })}
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-white" placeholder="trade.mabanque.com" />
          </label>
          <button onClick={save} className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white">Enregistrer</button>
          {msg && <p className="text-sm text-muted">{msg}</p>}
        </section>

        <section className="rounded-xl border border-border bg-surface p-5">
          <p className="mb-2 text-sm text-muted">Aperçu</p>
          <div className="flex items-center gap-3 rounded-lg p-4" style={{ background: b.primary_color + '22' }}>
            {b.logo_url ? <img src={b.logo_url} alt="logo" className="h-8 w-8 rounded" /> : <div className="h-8 w-8 rounded" style={{ background: b.primary_color }} />}
            <span className="text-lg font-bold text-white">{b.brand_name}</span>
          </div>
          {b.custom_domain && <p className="mt-3 text-xs text-muted">Servi sur : {b.custom_domain}</p>}
        </section>
      </div>
    </div>
  );
}

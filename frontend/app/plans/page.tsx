'use client';

import { useEffect, useState } from 'react';
import { api, PlanInfo } from '@/lib/api';

type Plan = { id: string; price: number; features: string[] };

const ORDER = ['free', 'starter', 'pro', 'elite'];

export default function PlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [current, setCurrent] = useState<PlanInfo | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);

  async function refresh() {
    const [p, c] = await Promise.all([api.plans(), api.myPlan()]);
    setPlans(p as Plan[]);
    setCurrent(c);
  }
  useEffect(() => {
    refresh().catch(() => {});
  }, []);

  async function choose(id: string) {
    setBusy(id);
    setMsg(null);
    try {
      const r = await api.upgrade(id);
      if (r.checkout_url) {
        window.location.href = r.checkout_url;
        return;
      }
      setMsg(`Plan « ${id} » activé.`);
      await refresh();
    } catch (e: any) {
      setMsg(e.message ?? 'Erreur');
    } finally {
      setBusy(null);
    }
  }

  const rank = (p: string) => ORDER.indexOf(p);

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Plans &amp; Abonnement</h1>
          {current && (
            <p className="text-sm text-muted">
              Plan actuel : <span className="uppercase text-white">{current.plan}</span>
            </p>
          )}
        </div>
        <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">
          ← Dashboard
        </a>
      </header>

      {msg && <p className="rounded-lg border border-border bg-surface p-3 text-sm text-white">{msg}</p>}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {plans.map((p) => {
          const isCurrent = current?.plan === p.id;
          const isDown = current ? rank(p.id) < rank(current.plan) : false;
          return (
            <div
              key={p.id}
              className={`flex flex-col rounded-xl border p-5 ${
                isCurrent ? 'border-accent bg-accent/5' : 'border-border bg-surface'
              }`}
            >
              <h2 className="text-lg font-semibold uppercase text-white">{p.id}</h2>
              <p className="my-2 text-3xl font-bold text-white">
                {p.price}$<span className="text-sm font-normal text-muted">/mois</span>
              </p>
              <ul className="mb-4 flex-1 space-y-1 text-sm text-gray-300">
                {p.features.map((f) => (
                  <li key={f}>✓ {f}</li>
                ))}
              </ul>
              <button
                disabled={isCurrent || isDown || busy === p.id}
                onClick={() => choose(p.id)}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-40"
              >
                {isCurrent ? 'Plan actuel' : isDown ? 'Inférieur' : busy === p.id ? '…' : 'Choisir'}
              </button>
            </div>
          );
        })}
      </div>

      <p className="text-xs text-muted">
        Paiement sécurisé via Stripe lorsque configuré ; sinon activation directe (mode démo).
      </p>
    </div>
  );
}

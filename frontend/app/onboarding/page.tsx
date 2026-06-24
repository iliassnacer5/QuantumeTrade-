'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { api } from '@/lib/api';

const PROFILES = [
  { id: 'conservative', label: 'Conservateur', desc: '0,5 % risque / trade' },
  { id: 'moderate', label: 'Modéré', desc: '1 % risque / trade' },
  { id: 'aggressive', label: 'Agressif', desc: '2 % risque / trade' },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [profile, setProfile] = useState('moderate');
  const [capital, setCapital] = useState(10000);
  const [watchlist, setWatchlist] = useState('BTC/USDT');
  const [error, setError] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    try {
      const symbols = watchlist
        .split(',')
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean);
      await api.onboard(profile, capital, symbols);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <form onSubmit={submit} className="w-full max-w-md space-y-5 rounded-xl border border-border bg-surface p-6">
        <h1 className="text-xl font-bold">Profil de trading</h1>

        <div>
          <label className="mb-2 block text-sm text-muted">Profil de risque</label>
          <div className="grid grid-cols-3 gap-2">
            {PROFILES.map((p) => (
              <button
                type="button"
                key={p.id}
                onClick={() => setProfile(p.id)}
                className={`rounded-lg border p-3 text-left text-xs ${
                  profile === p.id ? 'border-accent bg-buy-soft' : 'border-border'
                }`}
              >
                <div className="font-semibold">{p.label}</div>
                <div className="text-muted">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm text-muted">Capital (USDT)</label>
          <input
            type="number"
            value={capital}
            min={1}
            onChange={(e) => setCapital(Number(e.target.value))}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-accent"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm text-muted">Marchés suivis (séparés par des virgules)</label>
          <input
            value={watchlist}
            onChange={(e) => setWatchlist(e.target.value)}
            className="w-full rounded-lg border border-border bg-background px-3 py-2 font-mono outline-none focus:border-accent"
          />
        </div>

        {error && <p className="text-sm text-sell">{error}</p>}
        <button type="submit" className="w-full rounded-lg bg-accent py-2 font-semibold text-background hover:opacity-90">
          Accéder au dashboard
        </button>
      </form>
    </main>
  );
}

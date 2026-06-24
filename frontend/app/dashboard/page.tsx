'use client';

import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { Chart } from '@/components/Chart';
import { SignalCard } from '@/components/SignalCard';
import { api, clearToken, openSignalStream, type Me, type Signal } from '@/lib/api';

const TIMEFRAMES = ['scalp', 'intraday', 'swing', 'position'];

export default function DashboardPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [asset, setAsset] = useState('BTC/USDT');
  const [timeframe, setTimeframe] = useState('swing');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [live, setLive] = useState(false);
  const [selected, setSelected] = useState<Signal | null>(null);

  const load = useCallback(async () => {
    try {
      const [m, s] = await Promise.all([api.me(), api.listSignals()]);
      setMe(m);
      setAsset(m.watchlist[0] ?? 'BTC/USDT');
      setSignals(s);
    } catch {
      router.push('/login');
    }
  }, [router]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const ws = openSignalStream((sig) => {
      setSignals((prev) => [sig, ...prev]);
    });
    if (ws) {
      ws.onopen = () => setLive(true);
      ws.onclose = () => setLive(false);
    }
    return () => ws?.close();
  }, []);

  async function generate() {
    setLoading(true);
    setError('');
    try {
      const sig = await api.generate(asset, timeframe, false);
      // Le WS pousse aussi le signal ; on déduplique par sécurité.
      setSignals((prev) => (prev.some((p) => p.id === sig.id) ? prev : [sig, ...prev]));
      setSelected(sig);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur');
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    clearToken();
    router.push('/login');
  }

  return (
    <main className="mx-auto max-w-5xl p-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          {me && (
            <p className="text-xs text-muted">
              {me.email} · plan <span className="uppercase text-white">{me.plan}</span> · capital{' '}
              {me.capital} USDT · profil {me.risk_profile}
              <span className={`ml-2 ${live ? 'text-buy' : 'text-muted'}`}>{live ? '● live' : '○ hors-ligne'}</span>
            </p>
          )}
        </div>
        <button onClick={logout} className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">
          Déconnexion
        </button>
      </header>

      <section className="mb-6 flex flex-wrap items-end gap-3 rounded-xl border border-border bg-surface p-4">
        <div>
          <label className="mb-1 block text-xs text-muted">Actif</label>
          <input
            value={asset}
            onChange={(e) => setAsset(e.target.value.toUpperCase())}
            className="rounded-lg border border-border bg-background px-3 py-2 font-mono outline-none focus:border-accent"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted">Timeframe</label>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-accent"
          >
            {TIMEFRAMES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={generate}
          disabled={loading}
          className="rounded-lg bg-accent px-5 py-2 font-semibold text-background hover:opacity-90 disabled:opacity-50"
        >
          {loading ? 'Analyse...' : 'Générer un signal'}
        </button>
        {error && <p className="text-sm text-sell">{error}</p>}
      </section>

      <section className="mb-6">
        <Chart asset={asset} timeframe={timeframe} signal={selected} />
      </section>

      {signals.length === 0 ? (
        <p className="text-center text-muted">Aucun signal pour le moment. Générez votre premier signal.</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {signals.map((s, i) => (
            <button
              key={s.id ?? i}
              onClick={() => {
                setSelected(s);
                setAsset(s.asset);
              }}
              className={`text-left transition ${selected?.id === s.id ? 'ring-2 ring-accent rounded-xl' : ''}`}
            >
              <SignalCard s={s} />
            </button>
          ))}
        </div>
      )}

      <p className="mt-8 text-center text-[11px] text-muted">
        ⚠️ Aide à la décision, pas un conseil en investissement. Le trading comporte un risque élevé de perte.
      </p>
    </main>
  );
}

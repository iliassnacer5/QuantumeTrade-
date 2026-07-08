'use client';

/**
 * 🗺️ CARTE DE L'EDGE — la réponse à « où est-ce que je gagne ? », mesurée et remise à jour chaque nuit.
 * Chaque combo (stratégie × symbole × timeframe) est validé au walk-forward AVEC frais :
 *   🟢 alpha>0 + PF≥1,2 = exploitable (seuls combos autorisés à l'auto-trading papier)
 *   🟡 alpha>0          = à surveiller
 *   🔴 pas d'edge       = à éviter — s'abstenir est une décision.
 */
import { useEffect, useState } from 'react';
import { api, EdgeMap } from '@/lib/api';

const MARKET_LABEL: Record<string, string> = {
  crypto: '₿ Crypto', forex: '💱 Forex', stock: '📈 Actions', commodity: '🥇 Or & Métaux',
};

export default function EdgePage() {
  const [data, setData] = useState<EdgeMap | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  function load() {
    api.edgeMap().then(setData).catch((e) => setError(e.message));
  }
  useEffect(load, []);

  async function runNow() {
    setRunning(true);
    setError(null);
    try {
      setData(await api.runEdgeSweep());
    } catch (e: any) {
      setError(e.message?.includes('402') ? 'Réservé au plan Pro+.' : e.message);
    } finally {
      setRunning(false);
    }
  }

  const rows = (data?.rows ?? []).filter((r) => !statusFilter || r.status === statusFilter);
  const byMarket = rows.reduce((acc: Record<string, typeof rows>, r) => {
    (acc[r.market] ??= []).push(r);
    return acc;
  }, {});

  return (
    <div className="p-8 space-y-5">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white">🗺️ Carte de l&apos;edge</h1>
          <p className="text-sm text-muted">
            Où gagne-t-on <b className="text-white">vraiment</b> ? Chaque combo est validé au walk-forward
            (out-of-sample, frais inclus) et re-mesuré chaque nuit. L&apos;auto-trading papier ne prend que les 🟢.
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={runNow} disabled={running}
            className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50">
            {running ? 'Sweep en cours (1-3 min)…' : '🔄 Relancer le sweep'}
          </button>
          <a href="/dashboard" className="rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-surface">← Dashboard</a>
        </div>
      </header>

      {error && <p className="text-sell">{error}</p>}

      {data && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-lg border border-buy/40 bg-buy/10 px-3 py-1.5 text-sm text-buy">🟢 {data.greens} exploitables</span>
            <span className="rounded-lg border border-yellow-500/40 bg-yellow-500/10 px-3 py-1.5 text-sm text-yellow-300">🟡 {data.yellows} à surveiller</span>
            <span className="rounded-lg border border-sell/40 bg-sell/10 px-3 py-1.5 text-sm text-sell">🔴 {data.reds} sans edge</span>
            {data.generated_at && <span className="text-xs text-muted">MàJ : {new Date(data.generated_at).toLocaleString('fr-FR')}</span>}
          </div>
          <p className="text-sm text-white">{data.note}</p>

          <div className="flex gap-1">
            {[{ id: '', l: 'Tous' }, { id: 'green', l: '🟢 Verts' }, { id: 'yellow', l: '🟡 Jaunes' }, { id: 'red', l: '🔴 Rouges' }].map((f) => (
              <button key={f.id} onClick={() => setStatusFilter(f.id)}
                className={`rounded-lg border px-3 py-1 text-sm ${statusFilter === f.id ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-surface'}`}>
                {f.l}
              </button>
            ))}
          </div>

          {Object.entries(byMarket).map(([mkt, mrows]) => (
            <section key={mkt} className="rounded-xl border border-border bg-surface p-4">
              <h2 className="mb-2 text-sm font-semibold text-white">{MARKET_LABEL[mkt] ?? mkt}</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="text-muted">
                    <tr><th className="py-1">Statut</th><th>Stratégie</th><th>Symbole</th><th>TF</th><th>Alpha</th><th>PF</th><th>Réussite</th><th>Trades</th><th>Stabilité</th></tr>
                  </thead>
                  <tbody>
                    {mrows.map((r, i) => (
                      <tr key={i} className={`border-t border-border/40 ${r.status === 'green' ? 'bg-buy/5' : ''}`}>
                        <td className="py-1.5">{r.status === 'green' ? '🟢' : r.status === 'yellow' ? '🟡' : '🔴'}</td>
                        <td className="text-white">{r.strategy_name}</td>
                        <td className="font-mono text-white">{r.symbol}{!r.data_real && ' ⚠︎'}</td>
                        <td className="text-muted">{r.timeframe}</td>
                        <td className={r.alpha >= 0 ? 'text-buy' : 'text-sell'}>{r.alpha >= 0 ? '+' : ''}{r.alpha}%</td>
                        <td className={r.pf >= 1 ? 'text-buy' : 'text-sell'}>{r.pf}</td>
                        <td className="text-white">{r.win}%</td>
                        <td className="text-muted">{r.trades}</td>
                        <td className="text-muted">{r.green_streak ? `🟢×${r.green_streak}` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ))}
        </>
      )}

      <p className="text-[11px] text-muted">
        ⚠︎ = données synthétiques (repli) — combo à ignorer. Un 🟢 isolé peut être de la chance : la colonne
        Stabilité compte les sweeps verts consécutifs. Les performances passées ne préjugent pas des futures.
      </p>
    </div>
  );
}

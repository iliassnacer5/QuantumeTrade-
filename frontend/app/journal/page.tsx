'use client';

import { useEffect, useState } from 'react';
import { api, JournalEntry, JournalInsights, PlanInfo } from '@/lib/api';

export default function JournalPage() {
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [insights, setInsights] = useState<JournalInsights | null>(null);
  const [explanations, setExplanations] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [e, i] = await Promise.all([api.journalList(), api.journalInsights()]);
      setEntries(e);
      setInsights(i);
    } catch (err: any) {
      setError(err.message ?? 'Erreur');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    api.myPlan().then(setPlan).catch(() => {});
    load();
  }, []);

  async function close(id: string, outcome: string) {
    const pnlStr = prompt(`P&L réalisé pour ce trade (${outcome}) ?`, '0');
    if (pnlStr === null) return;
    await api.journalClose(id, outcome, parseFloat(pnlStr) || 0);
    load();
  }

  async function explain(id: string) {
    setExplanations((m) => ({ ...m, [id]: 'Analyse en cours…' }));
    const r = await api.journalExplain(id);
    setExplanations((m) => ({ ...m, [id]: r.explanation }));
  }

  const locked = plan && !plan.features.journal;
  if (locked)
    return (
      <div className="p-8">
        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-6 text-yellow-200">
          Le Journal d&apos;apprentissage est réservé au plan <b>Pro</b>.{' '}
          <a href="/plans" className="underline">Mettre à niveau</a>
        </div>
      </div>
    );

  if (loading) return <div className="p-8 text-white">Chargement…</div>;

  const badge = (o: string) =>
    o === 'win' ? 'bg-buy/20 text-buy' : o === 'loss' ? 'bg-sell/20 text-sell' : 'bg-muted/20 text-muted';

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Journal &amp; Apprentissage</h1>
        <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">
          ← Dashboard
        </a>
      </header>

      {error && <p className="text-sell">{error}</p>}

      {insights && (
        <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {[
            ['Trades clôturés', insights.stats.closed],
            ['Taux de réussite', `${insights.stats.win_rate}%`],
            ['P&L cumulé', insights.stats.total_pnl],
            ['Ouverts', insights.stats.open],
          ].map(([label, val]) => (
            <div key={label} className="rounded-xl border border-border bg-surface p-4">
              <p className="text-xs text-muted">{label}</p>
              <p className="mt-1 text-xl text-white">{val}</p>
            </div>
          ))}
        </section>
      )}

      {insights && Object.keys(insights.weight_multipliers).length > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-2 text-sm text-muted">Pondérations apprises (appliquées par le Master)</h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(insights.weight_multipliers).map(([agent, mult]) => (
              <span key={agent} className="rounded-lg bg-[#1A1A1A] px-3 py-1 text-xs text-gray-200">
                {agent} ×{mult.toFixed(2)}
              </span>
            ))}
          </div>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-white">Trades ({entries.length})</h2>
        {entries.length === 0 && <p className="text-muted">Aucune entrée. Génère un signal depuis le dashboard.</p>}
        {entries.map((e) => (
          <div key={e.id} className="rounded-xl border border-border bg-surface p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className="font-medium text-white">{e.symbol}</span>
                <span className="text-sm text-muted">{e.direction}</span>
                <span className={`rounded px-2 py-0.5 text-xs ${badge(e.outcome)}`}>{e.outcome}</span>
                {e.pnl != null && <span className="text-sm text-gray-300">P&L {e.pnl}</span>}
              </div>
              <div className="flex gap-2">
                {e.outcome === 'open' && (
                  <>
                    <button onClick={() => close(e.id, 'win')} className="rounded border border-buy/40 px-2 py-1 text-xs text-buy hover:bg-buy/10">
                      Gain
                    </button>
                    <button onClick={() => close(e.id, 'loss')} className="rounded border border-sell/40 px-2 py-1 text-xs text-sell hover:bg-sell/10">
                      Perte
                    </button>
                  </>
                )}
                <button onClick={() => explain(e.id)} className="rounded border border-border px-2 py-1 text-xs text-gray-200 hover:bg-[#1A1A1A]">
                  Expliquer (IA)
                </button>
              </div>
            </div>
            {explanations[e.id] && (
              <p className="mt-3 whitespace-pre-wrap rounded-lg bg-[#1A1A1A] p-3 text-sm text-gray-300">{explanations[e.id]}</p>
            )}
          </div>
        ))}
      </section>
    </div>
  );
}

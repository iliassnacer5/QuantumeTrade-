'use client';

import { useEffect, useState } from 'react';
import { api, TrackRecord, WalkForward } from '@/lib/api';
import { PageHeader, Button, RouteTabs, PROVE_TABS } from '@/components/ui';

const VERDICT_STYLE: Record<string, string> = {
  robuste: 'border-buy/40 bg-buy/5',
  fragile: 'border-yellow-500/40 bg-yellow-500/5',
  non_prouve: 'border-sell/40 bg-sell/5',
  insuffisant: 'border-border bg-surface',
};

function ValidationCard({ v }: { v: WalkForward }) {
  return (
    <div className={`rounded-xl border p-4 ${VERDICT_STYLE[v.verdict] ?? 'border-border bg-surface'}`}>
      <div className="flex items-center justify-between">
        <span className="font-mono font-semibold text-white">{v.symbol}</span>
        <span className="text-xs text-muted">{v.timeframe}</span>
      </div>
      <p className="mt-1 text-sm">{v.label}</p>
      <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-muted">
        <span>Segments profitables : <span className="text-white">{v.profitable_folds}/{v.folds_evaluated}</span></span>
        <span>Cohérence : <span className="text-white">{Math.round(v.consistency * 100)}%</span></span>
        <span>Réussite moy. : <span className="text-white">{v.avg_win_rate}%</span></span>
        <span>Profit factor moy. : <span className="text-white">{v.avg_profit_factor}</span></span>
        <span>P&L moy./segment : <span className={v.avg_pnl_pct >= 0 ? 'text-buy' : 'text-sell'}>{v.avg_pnl_pct}%</span></span>
        <span>Trades : <span className="text-white">{v.total_trades}</span></span>
      </div>
      {/* Détail par segment (out-of-sample) */}
      <div className="mt-3 space-y-1">
        {v.folds.filter((f) => f.trades > 0).map((f) => (
          <div key={f.fold} className="flex items-center justify-between rounded bg-background/60 px-2 py-1 text-[11px]">
            <span className="text-muted">{f.from} → {f.to}</span>
            <span className="text-muted">{f.trades} trades · {f.win_rate}%</span>
            <span className={f.profitable ? 'text-buy' : 'text-sell'}>{f.pnl_pct >= 0 ? '+' : ''}{f.pnl_pct}%</span>
          </div>
        ))}
      </div>
      {!v.data_real && <p className="mt-2 text-[11px] text-sell">⚠ Données synthétiques — aucune preuve réelle.</p>}
    </div>
  );
}

export default function TrackRecordPage() {
  const [data, setData] = useState<TrackRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(refresh = false) {
    setLoading(true);
    setError(null);
    try {
      setData(await api.trackRecord(refresh));
    } catch (e: any) {
      setError(e.message?.includes('402') ? 'Réservé au plan Pro+ (backtesting).' : e.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { load(); }, []);

  const obs = data?.observed;

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        title="Track Record"
        subtitle="Validation honnête : robustesse out-of-sample (walk-forward) + performance réellement observée."
        actions={
          <Button variant="secondary" size="sm" onClick={() => load(true)} loading={loading}>
            {loading ? '…' : 'Recalculer'}
          </Button>
        }
      />
      <RouteTabs items={PROVE_TABS} />

      {error && <p className="text-sell">{error}</p>}
      {loading && <p className="text-muted">Validation walk-forward en cours (backtests sur plusieurs périodes)…</p>}

      {data && !loading && (
        <>
          {/* Performance réellement observée (Journal) */}
          <section className="rounded-xl border border-border bg-surface p-4">
            <h2 className="mb-1 text-lg font-semibold text-white">Performance réellement observée</h2>
            <p className="mb-3 text-xs text-muted">
              Issue de tes signaux clôturés dans le Journal — c&apos;est le seul vrai « forward test ». Limité tant que peu de trades sont clôturés.
            </p>
            {obs && obs.closed > 0 ? (
              <div className="grid grid-cols-2 gap-2 text-sm md:grid-cols-4">
                <span className="text-muted">Trades clôturés : <span className="text-white">{obs.closed}</span></span>
                <span className="text-muted">Réussite : <span className={obs.win_rate >= 50 ? 'text-buy' : 'text-sell'}>{obs.win_rate}%</span></span>
                <span className="text-muted">Gagnants/Perdants : <span className="text-white">{obs.wins}/{obs.losses}</span></span>
                <span className="text-muted">P&L cumulé : <span className={obs.total_pnl >= 0 ? 'text-buy' : 'text-sell'}>{obs.total_pnl}</span></span>
              </div>
            ) : (
              <p className="text-sm text-muted">
                Aucun trade clôturé pour l&apos;instant. Génère des signaux et clôture-les dans le <a href="/journal" className="text-accent underline">Journal</a> pour bâtir un vrai track record.
              </p>
            )}
          </section>

          {/* Validation walk-forward */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">Validation walk-forward (out-of-sample)</h2>
              <span className="text-xs text-muted">{data.summary.robust}/{data.summary.symbols} jugés robustes</span>
            </div>
            <p className="text-xs text-muted">
              Chaque symbole est backtesté sur plusieurs périodes successives indépendantes. Un edge réel est régulier ;
              un résultat qui ne tient que sur une période est marqué « fragile » ou « non prouvé ».
            </p>
            <div className="grid gap-3 md:grid-cols-2">
              {data.validation.map((v) => <ValidationCard key={v.symbol} v={v} />)}
            </div>
          </section>

          <p className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-3 text-xs text-yellow-200">
            {data.disclaimer}
          </p>
        </>
      )}
    </div>
  );
}

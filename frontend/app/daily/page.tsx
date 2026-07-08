'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';

const TIMEFRAMES = [
  { tf: '5m', label: 'Scalp 5m' },
  { tf: '15m', label: 'Intraday 15m' },
  { tf: '1h', label: 'Swing 1h' },
  { tf: '4h', label: 'Position 4h' },
  { tf: '1d', label: 'Journalier 1d' },
];

export default function DailyPage() {
  const [data, setData] = useState<{ date: string; timeframe?: string; picks: any[]; generated_at: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tf, setTf] = useState('1h');

  async function load(refresh = false, timeframe = tf) {
    setLoading(true);
    setError(null);
    try {
      setData(await api.dailyPicks(refresh, timeframe));
    } catch (e: any) {
      setError(e.message?.includes('402') ? 'Réservé au plan Pro+ (utilise le backtest).' : e.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load(false, tf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tf]);

  const byMarket = (data?.picks ?? []).reduce((acc: Record<string, any[]>, p) => {
    (acc[p.asset_class] ??= []).push(p);
    return acc;
  }, {});
  const labels: Record<string, string> = { crypto: 'Crypto', forex: 'Forex', stock: 'Actions', commodity: '🥇 Or & Métaux' };

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Trades du jour</h1>
          <p className="text-sm text-muted">
            Les meilleures opportunités par marché : ★ <span className="text-buy">confirmées par backtest</span> en priorité,
            sinon les setups <span className="text-yellow-300">à surveiller</span> (non confirmés, clairement étiquetés).
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => load(true)} disabled={loading} className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface disabled:opacity-50">
            {loading ? '…' : 'Rafraîchir'}
          </button>
          <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">← Dashboard</a>
        </div>
      </header>

      {/* Sélecteur d'unité de temps : les TF longs (4h, 1d) filtrent le bruit -> plus fiables. */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted">Unité de temps</span>
        {TIMEFRAMES.map((t) => (
          <button key={t.tf} onClick={() => setTf(t.tf)}
            className={`rounded-lg border px-3 py-1 text-sm ${tf === t.tf ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-surface'}`}>
            {t.label}
          </button>
        ))}
        <span className="text-[11px] text-muted">Plus l&apos;unité est longue, moins il y a de bruit (signaux souvent plus fiables).</span>
      </div>

      {error && <p className="text-sell">{error}</p>}
      {loading && <p className="text-muted">Analyse des marchés en cours (scan + backtests)…</p>}

      {data && !loading && (
        <>
          <p className="text-xs text-muted">Sélection du {data.date} · {data.picks.length} trade(s) retenu(s)</p>
          {data.picks.length === 0 && (
            <div className="rounded-xl border border-border bg-surface p-6 text-muted">
              Aucun trade fiable à forte conviction aujourd&apos;hui. C&apos;est un signal en soi : mieux vaut s&apos;abstenir
              que forcer un mauvais trade.
            </div>
          )}
          {Object.entries(byMarket).map(([cls, picks]) => (
            <section key={cls} className="space-y-3">
              <h2 className="text-lg font-semibold text-white">{labels[cls] ?? cls}</h2>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                {picks.map((p) => {
                  const confirmed = p.tier === 'confirmed';
                  return (
                  <div key={p.symbol} className={`rounded-xl border bg-surface p-4 ${confirmed ? 'border-buy/40' : 'border-yellow-500/30'}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-semibold text-white">{p.symbol}</span>
                      <div className="flex items-center gap-1.5">
                        {p.timeframe && <span className="rounded bg-background px-1.5 py-0.5 text-[10px] text-muted">{p.timeframe}</span>}
                        <span className={`rounded px-2 py-0.5 text-xs font-bold ${p.direction === 'BUY' ? 'bg-buy/20 text-buy' : 'bg-sell/20 text-sell'}`}>{p.direction}</span>
                      </div>
                    </div>
                    <div className="mt-1">
                      {confirmed ? (
                        <span className="rounded bg-buy/15 px-2 py-0.5 text-[10px] font-bold text-buy">★ CONFIRMÉ PAR BACKTEST</span>
                      ) : (
                        <span className="rounded bg-yellow-500/15 px-2 py-0.5 text-[10px] font-bold text-yellow-300">👀 À SURVEILLER — non confirmé</span>
                      )}
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-muted">
                      <span>Prix : <span className="text-white">{p.price}</span></span>
                      <span>ADX : <span className="text-white">{p.adx}</span></span>
                      {p.backtest ? (
                        <>
                          <span>Réussite : <span className="text-buy">{p.backtest.win_rate}%</span></span>
                          <span>Profit factor : <span className="text-buy">{p.backtest.profit_factor}</span></span>
                          <span>P&L backtest : <span className="text-white">{p.backtest.total_pnl_pct}%</span></span>
                          <span>Max DD : <span className="text-white">{p.backtest.max_drawdown_pct}%</span></span>
                        </>
                      ) : (
                        <span className="col-span-2 text-yellow-300/80">Backtest non concluant — prudence, valide toi-même.</span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-gray-400">{p.trend}</p>
                    <a href={`/scanner`} className="mt-2 inline-block text-xs text-accent hover:underline">Analyser en détail →</a>
                  </div>
                  );
                })}
              </div>
            </section>
          ))}
        </>
      )}

      <p className="text-xs text-muted">
        Mis à jour automatiquement chaque matin. Active le digest dans Paramètres pour le recevoir par email/Telegram.
        Aide à la décision, pas un conseil en investissement.
      </p>
    </div>
  );
}

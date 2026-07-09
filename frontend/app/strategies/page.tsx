'use client';

import { useEffect, useState } from 'react';
import { api, StrategyInfo, StrategyBacktest, StrategySignal, WalkForward, MultiValidation, StrategyComparison } from '@/lib/api';
import { MarketSelector } from '@/components/domain';
import { PageHeader, RouteTabs, PROVE_TABS } from '@/components/ui';
import { MARKET_BADGE } from '@/lib/markets';

const VERDICT_STYLE: Record<string, string> = {
  robuste: 'text-buy', fragile: 'text-yellow-400', non_prouve: 'text-sell', insuffisant: 'text-muted',
};
const CAT_LABEL: Record<string, string> = {
  tendance: 'Tendance', 'retour-moyenne': 'Retour à la moyenne',
  volume: 'Volume', 'smart-money': 'Smart Money', cassure: 'Cassure',
};

export default function StrategiesPage() {
  const [list, setList] = useState<StrategyInfo[]>([]);
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [market, setMarket] = useState('crypto');
  const [timeframe, setTimeframe] = useState('1h');
  const [symbols, setSymbols] = useState<{ symbol: string }[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [bt, setBt] = useState<Record<string, StrategyBacktest>>({});
  const [wf, setWf] = useState<Record<string, WalkForward>>({});
  const [multi, setMulti] = useState<Record<string, MultiValidation>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [signal, setSignal] = useState<StrategySignal | null>(null);
  const [comparison, setComparison] = useState<StrategyComparison | null>(null);
  const [comparing, setComparing] = useState(false);
  const [autoTrade, setAutoTrade] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function toggleAutoTrade() {
    const r = await api.setAutoTrade(!autoTrade);
    setAutoTrade(r.auto_trade);
  }

  async function compareAll() {
    setComparing(true);
    setError(null);
    try {
      setComparison(await api.compareStrategies(symbol, timeframe));
    } catch (e: any) {
      setError(e.message?.includes('402') ? 'Réservé au plan Pro+.' : e.message);
    } finally {
      setComparing(false);
    }
  }

  useEffect(() => {
    api.strategies().then((d) => setList(d.strategies)).catch((e) => setError(e.message));
    api.selectedStrategy().then((d) => setSelected(d.selected)).catch(() => {});
    api.autoTrade().then((d) => setAutoTrade(d.auto_trade)).catch(() => {});
  }, []);

  // Symboles du marché choisi (crypto / forex / actions) — tous les marchés disponibles.
  useEffect(() => {
    api.symbols(undefined, market)
      .then((d) => {
        setSymbols(d.results);
        if (d.results.length && !d.results.some((r) => r.symbol === symbol)) setSymbol(d.results[0].symbol);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [market]);

  async function runBoth(id: string) {
    setBusy(id);
    setError(null);
    try {
      const [b, w] = await Promise.all([
        api.strategyBacktest(symbol, id, timeframe),
        api.strategyWalkForward(symbol, id, timeframe),
      ]);
      setBt((m) => ({ ...m, [id]: b }));
      setWf((m) => ({ ...m, [id]: w }));
    } catch (e: any) {
      setError(e.message?.includes('402') ? 'Réservé au plan Pro+ (backtesting).' : e.message);
    } finally {
      setBusy(null);
    }
  }

  async function validateMulti(id: string) {
    setBusy(id + '-multi');
    setError(null);
    try {
      const r = await api.strategyValidateMulti(id, timeframe, market);
      setMulti((m) => ({ ...m, [id]: r }));
    } catch (e: any) {
      setError(e.message?.includes('402') ? 'Réservé au plan Pro+.' : e.message);
    } finally {
      setBusy(null);
    }
  }

  async function choose(id: string) {
    await api.selectStrategy(id);
    setSelected(id);
  }

  async function genSignal(id: string) {
    setBusy(id + '-sig');
    setError(null);
    try {
      setSignal(await api.strategySignal(symbol, id, timeframe));
    } catch (e: any) {
      setError(e.message);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        title="Stratégies"
        subtitle="Backteste des stratégies éprouvées, valide-les (walk-forward) et choisis-en une pour travailler."
      />
      <RouteTabs items={PROVE_TABS} />

      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-muted">Marché</label>
        <MarketSelector value={market} onChange={setMarket} includeAll={false} label={null} />
        <label className="text-sm text-muted">Tester sur</label>
        <select value={symbol} onChange={(e) => setSymbol(e.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-1.5 font-mono text-sm text-white">
          {(symbols.length ? symbols : [{ symbol: 'BTC/USDT' }]).map((s) => <option key={s.symbol} value={s.symbol}>{s.symbol}</option>)}
        </select>
        <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm text-white" title="Le journalier (1d) couvre des années d'historique = validation plus fiable">
          <option value="1h">1h (court)</option>
          <option value="4h">4h</option>
          <option value="1d">Journalier (long, + fiable)</option>
        </select>
        {selected && <span className="text-sm text-muted">Stratégie active : <b className="text-accent">{selected}</b></span>}
        <button onClick={compareAll} disabled={comparing}
          className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50">
          {comparing ? 'Comparaison…' : '🏆 Comparer TOUTES les stratégies'}
        </button>
        <button onClick={toggleAutoTrade}
          title="Forward test : chaque signal de ta stratégie active ouvre automatiquement un trade papier (1% de risque, SL/TP, clôture auto). Résultats dans le Portefeuille."
          className={`rounded-lg border px-3 py-1.5 text-sm ${autoTrade ? 'border-buy bg-buy/15 text-buy' : 'border-border text-muted hover:bg-surface'}`}>
          {autoTrade ? '🤖 Trading auto papier : ON' : '🤖 Trading auto papier : OFF'}
        </button>
      </div>

      {error && <p className="text-sell">{error}</p>}

      {/* Comparaison de toutes les stratégies sur le symbole choisi */}
      {comparison && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-1 text-lg font-semibold text-white">Comparaison sur {comparison.symbol} ({comparison.timeframe})</h2>
          <p className="mb-3 text-sm">{comparison.note}</p>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-muted">
                <tr>
                  <th className="py-1">Stratégie</th><th>Alpha</th><th>PF</th><th>Réussite</th><th>P&L net</th><th>Trades</th><th>Max DD</th>
                </tr>
              </thead>
              <tbody>
                {comparison.ranking.map((r, i) => (
                  <tr key={r.id} className={`border-t border-border/40 ${i === 0 ? 'bg-buy/5' : ''}`}>
                    <td className="py-1.5 text-white">{i === 0 && '🏆 '}{r.name}</td>
                    <td className={r.alpha_pct >= 0 ? 'text-buy' : 'text-sell'}>{r.alpha_pct}%</td>
                    <td className={r.profit_factor >= 1 ? 'text-buy' : 'text-sell'}>{r.profit_factor}</td>
                    <td className="text-white">{r.win_rate}%</td>
                    <td className={r.pnl_pct >= 0 ? 'text-buy' : 'text-sell'}>{r.pnl_pct}%</td>
                    <td className="text-muted">{r.trades}</td>
                    <td className="text-muted">{r.max_drawdown_pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {comparison.recommended && (
            <button onClick={() => choose(comparison.recommended!.id)}
              className="mt-3 rounded-lg bg-buy px-3 py-1.5 text-sm font-medium text-white">
              Choisir la meilleure ({comparison.recommended.name})
            </button>
          )}
        </section>
      )}

      {signal && (
        <section className="rounded-xl border border-accent/40 bg-accent/5 p-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-white">
              Signal {signal.name} — {signal.symbol}
              {signal.timeframe && <span className="ml-2 rounded bg-background px-2 py-0.5 text-[11px] font-normal text-muted">⏱ {signal.timeframe}</span>}
            </h2>
            <span className={`rounded px-2 py-0.5 text-sm font-bold ${signal.direction === 'BUY' ? 'bg-buy/20 text-buy' : signal.direction === 'SELL' ? 'bg-sell/20 text-sell' : 'bg-border text-muted'}`}>{signal.direction}</span>
          </div>
          {signal.direction !== 'HOLD' ? (
            <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-muted md:grid-cols-4">
              <span>Entrée : <span className="text-white">{signal.entry}</span></span>
              <span>SL : <span className="text-sell">{signal.stop_loss}</span></span>
              <span>TP : <span className="text-buy">{signal.take_profit_1}</span></span>
              <span>R/R : <span className="text-white">1 : {signal.risk_reward}</span></span>
            </div>
          ) : <p className="mt-1 text-sm text-muted">{signal.rationale}</p>}
          <p className="mt-1 text-[11px] text-muted">Source données : {signal.data_source}. Aide à la décision, pas un conseil.</p>
        </section>
      )}

      <section className="grid gap-3 md:grid-cols-2">
        {list.map((s) => {
          const w = wf[s.id];
          const isSel = selected === s.id;
          const fits = !s.markets || s.markets.includes(market);
          return (
            <div key={s.id} className={`rounded-xl border p-4 ${isSel ? 'border-accent bg-accent/5' : 'border-border bg-surface'} ${fits ? '' : 'opacity-50'}`}
              title={fits ? '' : 'Stratégie non recommandée pour ce marché'}>
              <div className="flex items-start justify-between">
                <div>
                  <span className="font-semibold text-white">{s.name}</span>
                  <span className="ml-2 rounded bg-background px-2 py-0.5 text-[10px] text-muted">{CAT_LABEL[s.category] ?? s.category}</span>
                  {(s.markets ?? []).map((mk) => (
                    <span key={mk} className={`ml-1 rounded px-1.5 py-0.5 text-[10px] ${mk === market ? 'bg-accent/20 text-accent' : 'bg-background text-muted'}`}>
                      {MARKET_BADGE[mk] ?? mk}
                    </span>
                  ))}
                </div>
                {isSel && <span className="text-xs text-accent">✓ active</span>}
              </div>
              <p className="mt-1 text-xs text-muted">{s.description}</p>

              {bt[s.id] && (() => { const bb = bt[s.id]; const b2 = bb.metrics; return (
                <div className="mt-3 grid grid-cols-3 gap-1 text-xs text-muted">
                  <span>Réussite : <span className="text-white">{b2.win_rate}%</span></span>
                  <span>PF : <span className="text-white">{b2.profit_factor}</span></span>
                  <span>P&L net : <span className={b2.total_pnl_pct >= 0 ? 'text-buy' : 'text-sell'}>{b2.total_pnl_pct}%</span></span>
                  <span>Trades : <span className="text-white">{b2.trades}</span></span>
                  <span>Max DD : <span className="text-white">{b2.max_drawdown_pct}%</span></span>
                  <span title="Frais + slippage appliqués par côté">Coûts : <span className="text-white">{bb.cost_pct_per_side}%</span></span>
                  <span title="Acheter & garder sur la même période">Buy&amp;Hold : <span className="text-white">{bb.benchmark_pnl_pct}%</span></span>
                  <span className="col-span-2" title="Surperformance vs simplement détenir l'actif">
                    Alpha : <span className={(bb.alpha_pct ?? 0) >= 0 ? 'text-buy' : 'text-sell'}>{bb.alpha_pct}%</span>
                    {(bb.alpha_pct ?? 0) <= 0 && <span className="text-sell"> — ne bat pas le buy &amp; hold</span>}
                  </span>
                </div>
              ); })()}
              {w && (
                <p className="mt-2 text-xs">
                  Validation : <span className={VERDICT_STYLE[w.verdict]}>{w.label}</span>
                  <span className="text-muted"> ({w.profitable_folds}/{w.folds_evaluated} segments · bat le hold {w.beats_hold_folds ?? 0}/{w.folds_evaluated})</span>
                </p>
              )}
              {multi[s.id] && (
                <p className="mt-1 text-xs">
                  Multi-marchés : <span className="text-white">{multi[s.id].verdict}</span>
                  <span className="text-muted"> ({multi[s.id].robust} robuste / {multi[s.id].symbols} · bat le hold {multi[s.id].beats_hold})</span>
                </p>
              )}

              <div className="mt-3 flex flex-wrap gap-2">
                <button onClick={() => runBoth(s.id)} disabled={busy === s.id}
                  className="rounded-lg border border-border px-3 py-1 text-xs text-white hover:bg-background disabled:opacity-50">
                  {busy === s.id ? 'Test…' : 'Backtester + valider'}
                </button>
                <button onClick={() => validateMulti(s.id)} disabled={busy === s.id + '-multi'}
                  className="rounded-lg border border-border px-3 py-1 text-xs text-white hover:bg-background disabled:opacity-50">
                  {busy === s.id + '-multi' ? 'Multi…' : 'Valider multi-marchés'}
                </button>
                <button onClick={() => genSignal(s.id)} disabled={busy === s.id + '-sig'}
                  className="rounded-lg border border-border px-3 py-1 text-xs text-white hover:bg-background disabled:opacity-50">
                  {busy === s.id + '-sig' ? '…' : 'Signal live'}
                </button>
                <button onClick={() => choose(s.id)} disabled={isSel}
                  className="rounded-lg bg-accent px-3 py-1 text-xs font-medium text-white hover:opacity-90 disabled:opacity-50">
                  {isSel ? 'Choisie' : 'Choisir cette stratégie'}
                </button>
              </div>
            </div>
          );
        })}
      </section>

      <p className="text-xs text-muted">
        Conseil : ne « choisis » une stratégie que si sa validation walk-forward est ✅ robuste sur plusieurs symboles.
        Un bon backtest seul ne suffit pas — c&apos;est la régularité out-of-sample qui compte.
      </p>
    </div>
  );
}

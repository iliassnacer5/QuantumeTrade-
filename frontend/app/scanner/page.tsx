'use client';

import { useEffect, useMemo, useState } from 'react';
import { api, Signal } from '@/lib/api';
import { Chart } from '@/components/Chart';
import { SignalCard } from '@/components/SignalCard';

const CLASSES = [
  { id: '', label: 'Tous' },
  { id: 'crypto', label: 'Crypto' },
  { id: 'forex', label: 'Forex' },
  { id: 'stock', label: 'Actions' },
];
const TIMEFRAMES = [
  { tf: 'scalp', interval: '5m', label: 'Scalp (5m)' },
  { tf: 'intraday', interval: '15m', label: 'Intraday (15m)' },
  { tf: 'swing', interval: '1h', label: 'Swing (1h)' },
  { tf: 'position', interval: '4h', label: 'Position (4h)' },
];

export default function ScannerPage() {
  const [cls, setCls] = useState('crypto');
  const [symbols, setSymbols] = useState<{ symbol: string; asset_class: string }[]>([]);
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [tf, setTf] = useState('swing');
  const [hcOnly, setHcOnly] = useState(false);

  const [results, setResults] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const [scanned, setScanned] = useState(false);
  const [signal, setSignal] = useState<Signal | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<{ id: string; label: string; window_utc: string; open: boolean; symbol_count: number }[]>([]);
  const [utcTime, setUtcTime] = useState('');
  const [session, setSession] = useState<string>('');

  const interval = useMemo(() => TIMEFRAMES.find((t) => t.tf === tf)?.interval ?? '1h', [tf]);

  useEffect(() => {
    api.sessions().then((d) => { setSessions(d.sessions); setUtcTime(d.utc_time); }).catch(() => {});
  }, []);

  // Charge la liste des symboles selon la classe.
  useEffect(() => {
    api.symbols(undefined, cls || undefined)
      .then((d) => {
        setSymbols(d.results);
        if (d.results.length && !d.results.some((r) => r.symbol === symbol)) setSymbol(d.results[0].symbol);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cls]);

  async function scan() {
    setScanning(true);
    setError(null);
    try {
      const r = await api.scan(cls || undefined, interval, 30, hcOnly, session || undefined);
      setResults(r.results);
      setScanned(true);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setScanning(false);
    }
  }

  async function analyze(sym?: string) {
    const target = sym ?? symbol;
    if (sym) setSymbol(sym);
    setAnalyzing(true);
    setError(null);
    try {
      setSignal(await api.generate(target, tf, false));
    } catch (e: any) {
      setError(e.message?.includes('402') ? 'Limite de marchés du plan atteinte (passe en Pro/Elite).' : e.message);
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <div className="p-6 space-y-5">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Poste d&apos;analyse &amp; Scanner</h1>
          <p className="text-sm text-muted">Choisis marché, paire et timeframe — chart réel + analyse multi-agents.</p>
        </div>
        <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">← Dashboard</a>
      </header>

      {/* Sessions mondiales */}
      {sessions.length > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-semibold text-white">Sessions mondiales</span>
            <span className="text-xs text-muted">{utcTime}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button onClick={() => setSession('')}
              className={`rounded-lg border px-3 py-1.5 text-sm ${session === '' ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-background'}`}>
              Tous marchés
            </button>
            {sessions.map((s) => (
              <button key={s.id} onClick={() => setSession(s.id)}
                className={`rounded-lg border px-3 py-1.5 text-sm ${session === s.id ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-background'}`}>
                <span className={`mr-1.5 inline-block h-2 w-2 rounded-full ${s.open ? 'bg-buy' : 'bg-muted/40'}`} />
                {s.label} <span className="text-[10px] text-muted">({s.window_utc})</span>
                {s.open && <span className="ml-1 text-[10px] text-buy">● ouverte</span>}
              </button>
            ))}
          </div>
          {session && <p className="mt-2 text-xs text-muted">Le scan ne portera que sur les paires liquides de cette session.</p>}
        </section>
      )}

      {/* Sélecteurs */}
      <section className="flex flex-wrap items-end gap-3 rounded-xl border border-border bg-surface p-4">
        <div>
          <label className="mb-1 block text-xs text-muted">Marché</label>
          <div className="flex gap-1">
            {CLASSES.map((c) => (
              <button key={c.id} onClick={() => setCls(c.id)}
                className={`rounded-lg border px-3 py-1.5 text-sm ${cls === c.id ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-background'}`}>
                {c.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted">Paire / Symbole</label>
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-2 font-mono text-sm outline-none focus:border-accent">
            {symbols.map((s) => <option key={s.symbol} value={s.symbol}>{s.symbol}</option>)}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted">Timeframe</label>
          <select value={tf} onChange={(e) => setTf(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent">
            {TIMEFRAMES.map((t) => <option key={t.tf} value={t.tf}>{t.label}</option>)}
          </select>
        </div>
        <button onClick={() => analyze()} disabled={analyzing}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-50">
          {analyzing ? 'Analyse…' : 'Analyser ce symbole'}
        </button>
        <button onClick={scan} disabled={scanning}
          className="rounded-lg border border-border px-4 py-2 text-sm text-white hover:bg-background disabled:opacity-50">
          {scanning ? 'Scan…' : 'Scanner le marché'}
        </button>
        <label className="flex items-center gap-2 text-xs text-muted">
          <input type="checkbox" checked={hcOnly} onChange={(e) => setHcOnly(e.target.checked)} />
          Haute-conviction seulement
        </label>
      </section>

      {error && <p className="text-sell">{error}</p>}

      {/* Chart réel + carte signal */}
      <section className="grid gap-5 lg:grid-cols-2">
        <Chart asset={symbol} timeframe={tf} signal={signal} />
        <div>
          {signal ? <SignalCard s={signal} /> : (
            <div className="flex h-full min-h-[200px] items-center justify-center rounded-xl border border-dashed border-border text-sm text-muted">
              Clique « Analyser ce symbole » pour l&apos;analyse complète (métriques + multi-timeframe + news).
            </div>
          )}
        </div>
      </section>

      {/* Résultats du scan */}
      {scanned && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-white">
            Résultats du scan ({results.length}{results.length ? ` · ${results.filter((r) => r.high_conviction).length} haute-conviction` : ''})
          </h2>
          {results.length === 0 && <p className="text-muted">Aucun symbole ne correspond. Décoche « haute-conviction » pour voir tout le classement.</p>}
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {results.map((r) => (
              <button key={r.symbol} onClick={() => analyze(r.symbol)}
                className={`rounded-xl border bg-surface p-4 text-left transition hover:border-accent ${r.high_conviction ? 'border-buy/40' : 'border-border'}`}>
                <div className="flex items-center justify-between">
                  <span className="font-mono font-semibold text-white">{r.symbol}</span>
                  <span className={`rounded px-2 py-0.5 text-xs font-bold ${r.direction === 'BUY' ? 'bg-buy/20 text-buy' : r.direction === 'SELL' ? 'bg-sell/20 text-sell' : 'bg-border text-muted'}`}>{r.direction}</span>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-muted">
                  <span>Prix : <span className="text-white">{r.price}</span></span>
                  <span>ADX : <span className="text-white">{r.adx}</span></span>
                  <span>RSI : <span className="text-white">{r.rsi}</span></span>
                  <span>Conviction : <span className="text-white">{r.conviction}</span></span>
                </div>
                <p className="mt-1 text-xs text-gray-400">{r.trend}</p>
                {r.high_conviction && <span className="mt-2 inline-block rounded bg-buy/20 px-2 py-0.5 text-[10px] font-bold text-buy">★ HAUTE CONVICTION</span>}
              </button>
            ))}
          </div>
        </section>
      )}

      <p className="text-xs text-muted">Aide à la décision, pas un conseil en investissement. La haute conviction ne garantit pas le résultat.</p>
    </div>
  );
}

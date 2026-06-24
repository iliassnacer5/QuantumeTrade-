'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

const CLASSES = [
  { id: '', label: 'Tous' },
  { id: 'crypto', label: 'Crypto' },
  { id: 'forex', label: 'Forex' },
  { id: 'stock', label: 'Actions' },
];

export default function ScannerPage() {
  const [cls, setCls] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [scanned, setScanned] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function scan() {
    setLoading(true);
    setError(null);
    try {
      const r = await api.scan(cls || undefined, 20);
      setResults(r.results);
      setScanned(true);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Scanner haute-conviction</h1>
          <p className="text-sm text-muted">Uniquement les setups à tendance forte (ADX&gt;25) confirmés multi-timeframe.</p>
        </div>
        <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">← Dashboard</a>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        {CLASSES.map((c) => (
          <button key={c.id} onClick={() => setCls(c.id)}
            className={`rounded-lg border px-3 py-1 text-sm ${cls === c.id ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-surface'}`}>
            {c.label}
          </button>
        ))}
        <button onClick={scan} disabled={loading} className="ml-2 rounded-lg bg-accent px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50">
          {loading ? 'Scan en cours…' : 'Lancer le scan'}
        </button>
      </div>

      {error && <p className="text-sell">{error}</p>}

      {scanned && results.length === 0 && !loading && (
        <p className="text-muted">Aucun setup à forte conviction actuellement — le marché est en range. C&apos;est normal : mieux vaut attendre une vraie tendance.</p>
      )}

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {results.map((r) => (
          <div key={r.symbol} className="rounded-xl border border-border bg-surface p-4">
            <div className="flex items-center justify-between">
              <span className="font-mono font-semibold text-white">{r.symbol}</span>
              <span className={`rounded px-2 py-0.5 text-xs font-bold ${r.direction === 'BUY' ? 'bg-buy/20 text-buy' : 'bg-sell/20 text-sell'}`}>{r.direction}</span>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-1 text-xs text-muted">
              <span>Prix : <span className="text-white">{r.price}</span></span>
              <span>ADX : <span className="text-white">{r.adx}</span></span>
              <span>RSI : <span className="text-white">{r.rsi}</span></span>
              <span>MTF : <span className="text-white">{r.mtf.aligned}/{r.mtf.total}</span></span>
            </div>
            <p className="mt-2 text-xs text-gray-400">{r.trend}</p>
            <div className="mt-2 flex gap-1">
              {Object.entries(r.mtf.details).map(([tf, dir]: any) => (
                <span key={tf} className={`rounded px-1.5 py-0.5 text-[10px] ${dir === 'BUY' ? 'bg-buy/15 text-buy' : dir === 'SELL' ? 'bg-sell/15 text-sell' : 'bg-border text-muted'}`}>{tf} {dir}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-muted">Aide à la décision, pas un conseil en investissement. La haute conviction ne garantit pas le résultat.</p>
    </div>
  );
}

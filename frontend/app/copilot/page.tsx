'use client';

import { useEffect, useRef, useState } from 'react';
import { api, copilotStream, PlanInfo } from '@/lib/api';

type Msg = { role: 'user' | 'assistant'; content: string };

const CLASSES = [
  { id: '', label: 'Tous' },
  { id: 'crypto', label: 'Crypto' },
  { id: 'forex', label: 'Forex' },
  { id: 'stock', label: 'Actions' },
  { id: 'commodity', label: '🥇 Or & Métaux' },
];

// Actions rapides marché : pré-remplissent et envoient directement la question au copilot.
const QUICK_ACTIONS = [
  { label: '📊 État des marchés', q: 'Comment sont les marchés aujourd’hui ?' },
  { label: '🎯 Trades du jour', q: 'Quels trades je dois faire aujourd’hui ?' },
  { label: '🔍 Top crypto', q: 'Quelles sont les meilleures paires crypto à trader ?' },
  { label: '🔍 Top forex', q: 'Quelles sont les meilleures paires forex à trader ?' },
];

const SUGGESTIONS = [
  'Dois-je trader BTC maintenant ?',
  'Quels trades je dois faire aujourd’hui ?',
  'Comment sont les marchés ce matin ?',
  'Les meilleures opportunités sur les actions ?',
];

export default function CopilotPage() {
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Msg[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  // Sélecteur de marché / session / symbole.
  const [cls, setCls] = useState('crypto');
  const [session, setSession] = useState('');
  const [symbols, setSymbols] = useState<{ symbol: string; asset_class: string }[]>([]);
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [sessions, setSessions] = useState<{ id: string; label: string; window_utc: string; open: boolean }[]>([]);
  const [utcTime, setUtcTime] = useState('');

  useEffect(() => {
    api.myPlan().then(setPlan).catch(() => {});
    api.sessions().then((d) => { setSessions(d.sessions); setUtcTime(d.utc_time); }).catch(() => {});
  }, []);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Charge les symboles selon la classe et la session sélectionnées.
  useEffect(() => {
    api.symbols(undefined, cls || undefined, session || undefined)
      .then((d) => {
        setSymbols(d.results);
        if (d.results.length && !d.results.some((r) => r.symbol === symbol)) setSymbol(d.results[0].symbol);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cls, session]);

  const locked = plan && !plan.features.copilot;

  async function send(text?: string) {
    const question = (text ?? input).trim();
    if (!question || streaming || locked) return;
    setInput('');
    setError(null);
    setMessages((m) => [...m, { role: 'user', content: question }, { role: 'assistant', content: '' }]);
    setStreaming(true);
    try {
      await copilotStream(
        question,
        (delta) =>
          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = { role: 'assistant', content: copy[copy.length - 1].content + delta };
            return copy;
          }),
        undefined,
        symbol || undefined,
      );
    } catch (e: any) {
      setError(e.message ?? 'Erreur Copilot');
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-2rem)] max-w-3xl flex-col p-4">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Copilot</h1>
          <p className="text-sm text-muted">
            Ton copilot de trading : état des marchés, trades du jour, et « dois-je trader ce symbole ? ».
          </p>
        </div>
        <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">
          ← Dashboard
        </a>
      </header>

      {locked && (
        <div className="mb-4 rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-200">
          Le Copilot est réservé au plan <b>Pro</b>.{' '}
          <a href="/plans" className="underline">Mettre à niveau</a>
        </div>
      )}

      {/* Sélecteur : marché · session · symbole/paire */}
      <section className="mb-3 space-y-2 rounded-xl border border-border bg-surface p-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted">Marché</span>
          {CLASSES.map((c) => (
            <button
              key={c.id}
              onClick={() => setCls(c.id)}
              className={`rounded-lg border px-2.5 py-1 text-sm ${cls === c.id ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-background'}`}
            >
              {c.label}
            </button>
          ))}
        </div>
        {sessions.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-muted">Sessions <span className="text-[10px]">({utcTime})</span></span>
            <button
              onClick={() => setSession('')}
              className={`rounded-lg border px-2.5 py-1 text-sm ${session === '' ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-background'}`}
            >
              Toutes
            </button>
            {sessions.map((s) => (
              <button
                key={s.id}
                onClick={() => setSession(s.id)}
                className={`rounded-lg border px-2.5 py-1 text-sm ${session === s.id ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-background'}`}
              >
                <span className={`mr-1 inline-block h-2 w-2 rounded-full ${s.open ? 'bg-buy' : 'bg-muted/40'}`} />
                {s.label}
              </button>
            ))}
          </div>
        )}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted">Paire / Symbole</span>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-1.5 font-mono text-sm text-white outline-none focus:border-accent"
          >
            {symbols.map((s) => <option key={s.symbol} value={s.symbol}>{s.symbol}</option>)}
          </select>
          <button
            onClick={() => send(`Dois-je trader ${symbol} maintenant ?`)}
            disabled={!!locked || streaming}
            className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
          >
            ✅ Dois-je trader {symbol} ?
          </button>
        </div>
      </section>

      {/* Actions rapides marché */}
      <div className="mb-3 flex flex-wrap gap-2">
        {QUICK_ACTIONS.map((a) => (
          <button
            key={a.label}
            onClick={() => send(a.q)}
            disabled={!!locked || streaming}
            className="rounded-lg border border-border bg-surface px-3 py-1.5 text-sm text-white transition hover:border-accent disabled:opacity-50"
          >
            {a.label}
          </button>
        ))}
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-border bg-surface p-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-sm text-muted">
              Choisis un marché/symbole ci-dessus, clique une action rapide, ou pose ta question. Exemples :
            </p>
            <div className="flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  disabled={!!locked || streaming}
                  className="rounded-lg border border-border bg-background px-3 py-2 text-left text-sm text-gray-300 transition hover:border-accent hover:text-white disabled:opacity-50"
                >
                  « {s} »
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <div
              className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-xl px-4 py-2 text-sm ${
                m.role === 'user' ? 'bg-accent/20 text-white' : 'bg-[#1A1A1A] text-gray-200'
              }`}
            >
              {m.content || (streaming && i === messages.length - 1 ? '…' : '')}
            </div>
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {error && <p className="mt-2 text-sm text-sell">{error}</p>}

      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          disabled={!!locked || streaming}
          className="flex-1 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-white disabled:opacity-50"
          placeholder="Pose ta question… (ex. « dois-je trader SOL ? »)"
        />
        <button
          onClick={() => send()}
          disabled={!!locked || streaming}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {streaming ? '…' : 'Envoyer'}
        </button>
      </div>
    </div>
  );
}

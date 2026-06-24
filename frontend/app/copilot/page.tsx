'use client';

import { useEffect, useRef, useState } from 'react';
import { api, copilotStream, PlanInfo } from '@/lib/api';

type Msg = { role: 'user' | 'assistant'; content: string };

export default function CopilotPage() {
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [asset, setAsset] = useState('BTC/USDT');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Msg[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.myPlan().then(setPlan).catch(() => {});
  }, []);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const locked = plan && !plan.features.copilot;

  async function send() {
    if (!input.trim() || streaming) return;
    const question = input.trim();
    setInput('');
    setError(null);
    setMessages((m) => [...m, { role: 'user', content: question }, { role: 'assistant', content: '' }]);
    setStreaming(true);
    try {
      await copilotStream(
        asset,
        question,
        (delta) =>
          setMessages((m) => {
            const copy = [...m];
            copy[copy.length - 1] = { role: 'assistant', content: copy[copy.length - 1].content + delta };
            return copy;
          }),
      );
    } catch (e: any) {
      setError(e.message ?? 'Erreur Copilot');
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-2rem)] max-w-3xl flex-col p-4">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">AI Copilot</h1>
          <p className="text-sm text-muted">Interroge l&apos;analyse multi-agents d&apos;un actif.</p>
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

      <div className="mb-3 flex gap-2">
        <input
          value={asset}
          onChange={(e) => setAsset(e.target.value.toUpperCase())}
          className="w-40 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-white"
          placeholder="BTC/USDT"
        />
        <span className="self-center text-xs text-muted">Actif analysé</span>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-xl border border-border bg-surface p-4">
        {messages.length === 0 && (
          <p className="text-sm text-muted">
            Exemple : « Pourquoi le signal est-il en HOLD ? », « Quel agent pèse le plus ? »
          </p>
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
          placeholder="Pose ta question…"
        />
        <button
          onClick={send}
          disabled={!!locked || streaming}
          className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
        >
          {streaming ? '…' : 'Envoyer'}
        </button>
      </div>
    </div>
  );
}

'use client';

import { useEffect, useState } from 'react';
import { api, BrokerConn, Order, PlanInfo } from '@/lib/api';

export default function ExecutionPage() {
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [kyc, setKyc] = useState<string>('none');
  const [conns, setConns] = useState<BrokerConn[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const [k, c, o] = await Promise.all([api.kycStatus(), api.brokers(), api.orders()]);
      setKyc(k.status);
      setConns(c);
      setOrders(o);
    } catch (e: any) {
      setError(e.message);
    }
  }
  useEffect(() => {
    api.myPlan().then(setPlan).catch(() => {});
    api.kycStatus().then((k) => setKyc(k.status)).catch(() => {});
    load();
  }, []);

  const liveAllowed = !!plan?.features.auto_execution;

  async function submitKyc() {
    const name = prompt('Nom légal complet ?');
    if (!name) return;
    const country = prompt('Pays (ex: FR) ?') ?? '';
    const doc = prompt('N° pièce d’identité ?') ?? '';
    const r = await api.kycSubmit(name, country, doc);
    setKyc(r.status);
  }
  async function connect(mode: string) {
    try {
      if (mode === 'live') {
        const key = prompt('Clé API broker (Alpaca) ?') ?? '';
        const secret = prompt('Secret API ?') ?? '';
        await api.connectBroker('alpaca', 'live', key, secret);
      } else {
        await api.connectBroker('paper', 'paper');
      }
      load();
    } catch (e: any) {
      setError(e.message);
    }
  }
  async function order(conn: BrokerConn, side: string) {
    const symbol = prompt('Actif ?', 'BTC/USDT') ?? 'BTC/USDT';
    const qty = parseFloat(prompt('Quantité ?', '0.01') ?? '0');
    if (!qty) return;
    try {
      await api.placeOrder(conn.id, symbol, side, qty);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  }

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Exécution broker</h1>
          <p className="text-sm text-muted">Mode papier <b className="text-buy">gratuit</b> pour s&apos;entraîner. Réel = Elite + KYC.</p>
        </div>
        <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">← Dashboard</a>
      </header>

      {error && <p className="text-sell">{error}</p>}

      <section className="rounded-xl border border-border bg-surface p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-white">Statut KYC / AML</h2>
            <p className="text-sm text-muted">Requis pour l&apos;exécution réelle.</p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`rounded px-2 py-1 text-xs ${kyc === 'verified' ? 'bg-buy/20 text-buy' : 'bg-muted/20 text-muted'}`}>{kyc}</span>
            {kyc !== 'verified' && (
              <button onClick={submitKyc} className="rounded-lg bg-accent px-3 py-1 text-sm text-white">Soumettre KYC</button>
            )}
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Connexions broker</h2>
          <div className="flex gap-2">
            <button onClick={() => connect('paper')} className="rounded-lg border border-buy/40 bg-buy/10 px-3 py-1 text-sm text-buy hover:bg-buy/20">+ Papier (gratuit)</button>
            <button onClick={() => connect('live')} disabled={!liveAllowed || kyc !== 'verified'}
              title={!liveAllowed ? 'Réservé au plan Elite' : kyc !== 'verified' ? 'KYC requis' : ''}
              className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface disabled:opacity-40">+ Réel (Alpaca)</button>
          </div>
        </div>
        {conns.length === 0 && <p className="text-muted">Aucune connexion. Ajoute un broker papier pour commencer sans risque.</p>}
        {conns.map((c) => (
          <div key={c.id} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-surface p-4">
            <div className="flex items-center gap-3">
              <span className="font-medium text-white capitalize">{c.broker}</span>
              <span className={`rounded px-2 py-0.5 text-xs ${c.mode === 'live' ? 'bg-sell/20 text-sell' : 'bg-buy/20 text-buy'}`}>{c.mode}</span>
              {c.key_hint && <span className="font-mono text-xs text-muted">{c.key_hint}</span>}
            </div>
            <div className="flex gap-2">
              <button onClick={() => order(c, 'buy')} className="rounded border border-buy/40 px-2 py-1 text-xs text-buy hover:bg-buy/10">Acheter</button>
              <button onClick={() => order(c, 'sell')} className="rounded border border-sell/40 px-2 py-1 text-xs text-sell hover:bg-sell/10">Vendre</button>
              <button onClick={() => api.revokeBroker(c.id).then(load)} className="rounded border border-border px-2 py-1 text-xs text-muted hover:bg-[#1A1A1A]">Révoquer</button>
            </div>
          </div>
        ))}
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold text-white">Ordres ({orders.length})</h2>
        {orders.map((o) => (
          <div key={o.id} className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-surface p-3 text-sm">
            <span className="text-white">{o.symbol}</span>
            <span className={o.side === 'buy' ? 'text-buy' : 'text-sell'}>{o.side}</span>
            <span className="text-muted">{o.qty} @ {o.filled_price ?? '—'}</span>
            <span className="rounded bg-muted/20 px-2 py-0.5 text-xs text-muted">{o.mode}</span>
            <span className="text-xs text-gray-400">{o.status}</span>
            {o.copied_from && <span className="rounded bg-accent/20 px-2 py-0.5 text-xs text-accent">copié</span>}
          </div>
        ))}
      </section>
    </div>
  );
}

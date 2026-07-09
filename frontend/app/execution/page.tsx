'use client';

import { useEffect, useMemo, useState } from 'react';
import { api, BrokerConn, Order, PlanInfo } from '@/lib/api';
import { MarketSelector, OutcomeBanner, DataSourceBadge } from '@/components/domain';
import { PageHeader } from '@/components/ui';

type Ticket = { connId: string; side: 'buy' | 'sell' };

export default function ExecutionPage() {
  const [plan, setPlan] = useState<PlanInfo | null>(null);
  const [kyc, setKyc] = useState<string>('none');
  const [conns, setConns] = useState<BrokerConn[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Ticket d'ordre (formulaire complet : entrée, SL, TP, taille).
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [cls, setCls] = useState('crypto');
  const [session, setSession] = useState('');
  const [symbols, setSymbols] = useState<{ symbol: string; asset_class: string }[]>([]);
  const [sessions, setSessions] = useState<{ id: string; label: string; window_utc: string; open: boolean }[]>([]);
  const [utcTime, setUtcTime] = useState('');
  const [qty, setQty] = useState('0.01');
  const [stopLoss, setStopLoss] = useState('');
  const [takeProfit, setTakeProfit] = useState('');
  const [price, setPrice] = useState<number | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [checks, setChecks] = useState<Record<string, Order>>({});
  const [checking, setChecking] = useState<string | null>(null);
  const [dataSrc, setDataSrc] = useState<{ source: string; real: boolean; label: string } | null>(null);

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
    api.sessions().then((d) => { setSessions(d.sessions); setUtcTime(d.utc_time); }).catch(() => {});
    load();
    // Rafraîchit régulièrement pour refléter les clôtures automatiques (moniteur de positions).
    const id = setInterval(() => api.orders().then(setOrders).catch(() => {}), 45000);
    return () => clearInterval(id);
  }, []);

  // Charge les symboles selon le marché et la session sélectionnés.
  useEffect(() => {
    api.symbols(undefined, cls || undefined, session || undefined)
      .then((d) => {
        setSymbols(d.results);
        if (d.results.length && !d.results.some((r) => r.symbol === symbol)) setSymbol(d.results[0].symbol);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cls, session]);

  // Récupère le prix courant (≈ prix d'entrée) + la qualité des données quand on ouvre un ticket.
  useEffect(() => {
    if (!ticket) return;
    setPrice(null);
    setDataSrc(null);
    api.ohlcv(symbol, 'swing')
      .then((candles) => setPrice(candles.length ? candles[candles.length - 1].close : null))
      .catch(() => setPrice(null));
    api.dataSource(symbol).then(setDataSrc).catch(() => setDataSrc(null));
  }, [ticket, symbol]);

  const liveAllowed = !!plan?.features.auto_execution;

  // Aperçu live du trade (R/R, risque, gain potentiel) à partir du prix courant.
  const preview = useMemo(() => {
    const e = price;
    const sl = parseFloat(stopLoss);
    const tp = parseFloat(takeProfit);
    const q = parseFloat(qty);
    if (!e || !ticket) return null;
    const side = ticket.side;
    const slOk = !stopLoss || (side === 'buy' ? sl < e : sl > e);
    const tpOk = !takeProfit || (side === 'buy' ? tp > e : tp < e);
    const riskUnit = stopLoss ? Math.abs(e - sl) : null;
    const rewardUnit = takeProfit ? Math.abs(tp - e) : null;
    return {
      entry: e,
      slOk, tpOk,
      risk: riskUnit && q ? riskUnit * q : null,
      reward: rewardUnit && q ? rewardUnit * q : null,
      rr: riskUnit && rewardUnit ? rewardUnit / riskUnit : null,
    };
  }, [price, stopLoss, takeProfit, qty, ticket]);

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

  function openTicket(conn: BrokerConn, side: 'buy' | 'sell') {
    setError(null);
    setTicket({ connId: conn.id, side });
    setStopLoss('');
    setTakeProfit('');
  }

  async function manualClose(id: string) {
    if (!confirm('Clôturer cette position au prix du marché actuel ?')) return;
    setChecking(id);
    setError(null);
    try {
      await api.closeOrder(id);
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setChecking(null);
    }
  }

  async function verify(id: string) {
    setChecking(id);
    setError(null);
    try {
      const r = await api.checkOrder(id);
      setChecks((prev) => ({ ...prev, [id]: r }));
      if (r.outcome === 'won' || r.outcome === 'lost') load(); // clôture persistée
    } catch (e: any) {
      setError(e.message);
    } finally {
      setChecking(null);
    }
  }

  async function confirmOrder() {
    if (!ticket) return;
    const q = parseFloat(qty);
    if (!q || q <= 0) { setError('Quantité invalide.'); return; }
    if (preview && ((stopLoss && !preview.slOk) || (takeProfit && !preview.tpOk))) {
      setError(ticket.side === 'buy'
        ? 'Achat : le stop loss doit être sous l’entrée et le take profit au-dessus.'
        : 'Vente : le stop loss doit être au-dessus de l’entrée et le take profit en dessous.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await api.placeOrder(
        ticket.connId, symbol, ticket.side, q,
        stopLoss ? parseFloat(stopLoss) : null,
        takeProfit ? parseFloat(takeProfit) : null,
      );
      setTicket(null);
      load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-8 space-y-6">
      <PageHeader
        title="Paper Trading"
        subtitle={
          <>
            Trading simulé <b className="text-buy">gratuit</b> pour s’entraîner sans risque. Exécution réelle = Elite + KYC.
          </>
        }
      />

      {error && <p className="text-sell">{error}</p>}

      <section className="rounded-xl border border-border bg-surface p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-white">Statut KYC / AML</h2>
            <p className="text-sm text-muted">Requis pour l&apos;exécution réelle uniquement (le papier est libre).</p>
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
          <div key={c.id} className="rounded-xl border border-border bg-surface p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <span className="font-medium text-white capitalize">{c.broker}</span>
                <span className={`rounded px-2 py-0.5 text-xs ${c.mode === 'live' ? 'bg-sell/20 text-sell' : 'bg-buy/20 text-buy'}`}>{c.mode}</span>
                {c.key_hint && <span className="font-mono text-xs text-muted">{c.key_hint}</span>}
              </div>
              <div className="flex gap-2">
                <button onClick={() => openTicket(c, 'buy')} className="rounded border border-buy/40 px-3 py-1 text-xs text-buy hover:bg-buy/10">Acheter</button>
                <button onClick={() => openTicket(c, 'sell')} className="rounded border border-sell/40 px-3 py-1 text-xs text-sell hover:bg-sell/10">Vendre</button>
                <button onClick={() => api.revokeBroker(c.id).then(load)} className="rounded border border-border px-3 py-1 text-xs text-muted hover:bg-[#1A1A1A]">Révoquer</button>
              </div>
            </div>

            {/* Ticket d'ordre complet pour cette connexion */}
            {ticket?.connId === c.id && (
              <>
                <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm" onClick={() => setTicket(null)} />
                <aside className="fixed right-0 top-0 z-50 flex h-full w-full max-w-md flex-col overflow-y-auto border-l border-border bg-elevated p-5 shadow-elevated">
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-white">
                    Nouvel ordre — <span className={ticket.side === 'buy' ? 'text-buy' : 'text-sell'}>{ticket.side === 'buy' ? 'ACHAT' : 'VENTE'}</span>
                  </h3>
                  <button onClick={() => setTicket(null)} className="text-xs text-muted hover:text-white">✕ Fermer</button>
                </div>

                {/* Sélecteur complet : marché · session · paire/symbole */}
                <div className="mb-3 space-y-2">
                  <MarketSelector value={cls} onChange={setCls} />
                  {sessions.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-xs text-muted">Session <span className="text-[10px]">({utcTime})</span></span>
                      <button onClick={() => setSession('')}
                        className={`rounded border px-2 py-0.5 text-xs ${session === '' ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-surface'}`}>
                        Toutes
                      </button>
                      {sessions.map((ss) => (
                        <button key={ss.id} onClick={() => setSession(ss.id)}
                          className={`rounded border px-2 py-0.5 text-xs ${session === ss.id ? 'border-accent bg-accent/10 text-white' : 'border-border text-muted hover:bg-surface'}`}>
                          <span className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${ss.open ? 'bg-buy' : 'bg-muted/40'}`} />
                          {ss.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                  <label className="block">
                    <span className="mb-1 block text-xs text-muted">Paire / Symbole</span>
                    <select value={symbol} onChange={(e) => setSymbol(e.target.value)}
                      className="w-full rounded border border-border bg-surface px-2 py-1.5 font-mono text-sm text-white outline-none focus:border-accent">
                      {symbols.map((s) => <option key={s.symbol} value={s.symbol}>{s.symbol}</option>)}
                    </select>
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs text-muted">Quantité</span>
                    <input value={qty} onChange={(e) => setQty(e.target.value)} inputMode="decimal"
                      className="w-full rounded border border-border bg-surface px-2 py-1.5 text-sm text-white" />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs text-muted">Stop loss</span>
                    <input value={stopLoss} onChange={(e) => setStopLoss(e.target.value)} inputMode="decimal" placeholder="optionnel"
                      className={`w-full rounded border bg-surface px-2 py-1.5 text-sm text-white ${stopLoss && preview && !preview.slOk ? 'border-sell' : 'border-border'}`} />
                  </label>
                  <label className="block">
                    <span className="mb-1 block text-xs text-muted">Take profit</span>
                    <input value={takeProfit} onChange={(e) => setTakeProfit(e.target.value)} inputMode="decimal" placeholder="optionnel"
                      className={`w-full rounded border bg-surface px-2 py-1.5 text-sm text-white ${takeProfit && preview && !preview.tpOk ? 'border-sell' : 'border-border'}`} />
                  </label>
                </div>

                {/* Badge qualité des données */}
                {dataSrc && (
                  <div className="mt-3">
                    <DataSourceBadge real={dataSrc.real} label={dataSrc.real ? `${dataSrc.label} — données réelles` : `${dataSrc.label} — pas de source réelle, trade bloqué`} />
                  </div>
                )}

                {/* Aperçu du trade */}
                <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs md:grid-cols-4">
                  <span className="text-muted">Prix d&apos;entrée ≈ <span className="text-white">{price ?? '…'}</span></span>
                  <span className="text-muted">R/R : <span className="text-white">{preview?.rr ? `1 : ${preview.rr.toFixed(2)}` : '—'}</span></span>
                  <span className="text-muted">Risque : <span className="text-sell">{preview?.risk != null ? preview.risk.toFixed(2) : '—'}</span></span>
                  <span className="text-muted">Gain potentiel : <span className="text-buy">{preview?.reward != null ? preview.reward.toFixed(2) : '—'}</span></span>
                </div>

                <div className="mt-3 flex items-center gap-2">
                  <button onClick={confirmOrder} disabled={submitting || dataSrc?.real === false}
                    title={dataSrc?.real === false ? 'Données synthétiques : trade désactivé' : ''}
                    className={`rounded-lg px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50 ${ticket.side === 'buy' ? 'bg-buy' : 'bg-sell'}`}>
                    {submitting ? '…' : ticket.side === 'buy' ? 'Confirmer l’achat' : 'Confirmer la vente'}
                  </button>
                  <span className="text-[11px] text-muted">Ordre simulé — rempli au prix marché. Le stop/TP sont enregistrés avec le trade.</span>
                </div>
                </aside>
              </>
            )}
          </div>
        ))}
      </section>

      <section className="space-y-2">
        <h2 className="text-lg font-semibold text-white">Ordres ({orders.length})</h2>
        {orders.map((o) => {
          const chk = checks[o.id];
          const outcome = o.outcome ?? chk?.outcome;       // clôturé (persisté) ou dernière vérif
          const hasLevels = o.stop_loss != null || o.take_profit != null;
          const closed = outcome === 'won' || outcome === 'lost';
          return (
            <div key={o.id} className="rounded-lg border border-border bg-surface p-3 text-sm">
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-mono text-white">{o.symbol}</span>
                <span className={o.side === 'buy' ? 'text-buy' : 'text-sell'}>{o.side}</span>
                <span className="text-muted">{o.qty} @ {o.filled_price ?? '—'}</span>
                <span className="rounded bg-muted/20 px-2 py-0.5 text-xs text-muted">{o.mode}</span>
                {outcome ? (
                  <OutcomeBanner outcome={outcome} className="px-2 py-0.5" />
                ) : (
                  <span className="text-xs text-gray-400">{o.status}</span>
                )}
                {o.copied_from && <span className="rounded bg-accent/20 px-2 py-0.5 text-xs text-accent">copié</span>}
                {!closed && (
                  <div className="ml-auto flex gap-2">
                    {hasLevels && (
                      <button onClick={() => verify(o.id)} disabled={checking === o.id}
                        className="rounded border border-accent/50 px-2 py-0.5 text-xs text-accent hover:bg-accent/10 disabled:opacity-50">
                        {checking === o.id ? '…' : 'Vérifier'}
                      </button>
                    )}
                    <button onClick={() => manualClose(o.id)} disabled={checking === o.id}
                      className="rounded border border-sell/50 px-2 py-0.5 text-xs text-sell hover:bg-sell/10 disabled:opacity-50">
                      {checking === o.id ? '…' : 'Clôturer'}
                    </button>
                  </div>
                )}
              </div>
              {hasLevels && (
                <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-muted">
                  {o.stop_loss != null && <span>SL : <span className="text-sell">{o.stop_loss}</span></span>}
                  {o.take_profit != null && <span>TP : <span className="text-buy">{o.take_profit}</span></span>}
                  {o.risk_reward != null && <span>R/R : <span className="text-white">1 : {o.risk_reward}</span></span>}
                  {o.risk_amount != null && <span>Risque : <span className="text-sell">{o.risk_amount}</span></span>}
                  {o.potential_profit != null && <span>Gain potentiel : <span className="text-buy">{o.potential_profit}</span></span>}
                </div>
              )}
              {/* Résultat de la vérification */}
              {closed && (o.realized_pnl ?? chk?.realized_pnl) != null && (
                <p className="mt-1.5 text-xs">
                  Sortie @ {o.exit_price ?? chk?.exit_price} · P&L réalisé :{' '}
                  <span className={(o.realized_pnl ?? chk?.realized_pnl)! >= 0 ? 'text-buy' : 'text-sell'}>
                    {(o.realized_pnl ?? chk?.realized_pnl)! >= 0 ? '+' : ''}{o.realized_pnl ?? chk?.realized_pnl}
                  </span>
                </p>
              )}
              {chk?.outcome === 'open' && (
                <p className="mt-1.5 text-xs text-muted">
                  Trade encore ouvert · prix actuel {chk.current_price} · P&L latent :{' '}
                  <span className={(chk.unrealized_pnl ?? 0) >= 0 ? 'text-buy' : 'text-sell'}>
                    {(chk.unrealized_pnl ?? 0) >= 0 ? '+' : ''}{chk.unrealized_pnl}
                  </span>
                  {chk.note && <span className="ml-1">· {chk.note}</span>}
                </p>
              )}
            </div>
          );
        })}
      </section>
    </div>
  );
}

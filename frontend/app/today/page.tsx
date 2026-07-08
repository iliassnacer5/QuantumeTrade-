'use client';

/**
 * « Ma journée » — le briefing du matin en 30 secondes.
 * Régime du jour · ce qui s'est passé sur mes positions · les meilleures opportunités ·
 * mon track record réel · ce que les filtres m'ont évité. Le rituel quotidien du trader.
 */
import { useEffect, useState } from 'react';
import { api, MarketRegime, SignalsTrackRecord, Wallet } from '@/lib/api';

export default function TodayPage() {
  const [regime, setRegime] = useState<MarketRegime | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [track, setTrack] = useState<SignalsTrackRecord | null>(null);
  const [picks, setPicks] = useState<any[] | null>(null);
  const [picksLocked, setPicksLocked] = useState(false);

  useEffect(() => {
    api.marketRegime().then(setRegime).catch(() => {});
    api.wallet().then(setWallet).catch(() => {});
    api.signalsTrackRecord().then(setTrack).catch(() => {});
    api.dailyPicks(false, '4h')
      .then((d) => setPicks(d.picks.slice(0, 3)))
      .catch((e) => { if (String(e.message).includes('402')) setPicksLocked(true); });
  }, []);

  const today = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });
  const regimeTone = regime?.regime === 'on' ? 'border-buy/40 bg-buy/5' : regime?.regime === 'off' ? 'border-sell/40 bg-sell/5' : 'border-border bg-surface';
  const closedRecently = (wallet?.equity_curve ?? []).slice(-3).reverse();
  const obs = track?.observed;
  const av = track?.avoided;

  return (
    <div className="mx-auto max-w-4xl space-y-5 p-6">
      <header>
        <h1 className="text-2xl font-bold text-white">☀️ Ma journée</h1>
        <p className="text-sm capitalize text-muted">{today} · ton briefing en 30 secondes</p>
      </header>

      {/* 1. Le régime du jour */}
      <section className={`rounded-xl border p-4 ${regimeTone}`}>
        <h2 className="mb-1 text-sm font-semibold text-white">🌍 Le marché aujourd&apos;hui</h2>
        {regime ? (
          <>
            <p className="text-sm text-gray-200">{regime.regime_label}</p>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-muted">
              <span>Sessions ouvertes : <b className="text-white">{regime.open_sessions.join(', ') || 'aucune'}</b></span>
              {regime.inflation != null && <span>· Inflation {regime.inflation}%</span>}
              {regime.rate_trend && <span>· Taux : {regime.rate_trend}</span>}
              <span className="text-[11px]">({regime.utc_time})</span>
            </div>
          </>
        ) : <p className="text-sm text-muted">Chargement…</p>}
      </section>

      {/* 2. Mes positions / ce qui s'est passé */}
      <section className="rounded-xl border border-border bg-surface p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">💼 Mon portefeuille</h2>
          <a href="/wallet" className="text-xs text-accent hover:underline">détail →</a>
        </div>
        {wallet ? (
          <>
            <div className="mt-2 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
              <div><p className="text-xs text-muted">Équité</p><p className="font-semibold text-white">{wallet.equity.toLocaleString()} $</p></div>
              <div><p className="text-xs text-muted">Performance</p><p className={`font-semibold ${wallet.return_pct >= 0 ? 'text-buy' : 'text-sell'}`}>{wallet.return_pct >= 0 ? '+' : ''}{wallet.return_pct}%</p></div>
              <div><p className="text-xs text-muted">Positions ouvertes</p><p className="font-semibold text-white">{wallet.stats.open_positions}</p></div>
              <div><p className="text-xs text-muted">Réussite</p><p className={`font-semibold ${wallet.stats.win_rate >= 50 ? 'text-buy' : 'text-white'}`}>{wallet.stats.win_rate}%</p></div>
            </div>
            {closedRecently.length > 0 && (
              <div className="mt-3 space-y-1">
                <p className="text-xs text-muted">Dernières clôtures :</p>
                {closedRecently.map((c, i) => (
                  <p key={i} className="text-xs">
                    <span className={c.outcome === 'won' ? 'text-buy' : 'text-sell'}>{c.outcome === 'won' ? '✅' : '🔴'}</span>{' '}
                    <span className="font-mono text-white">{c.symbol}</span>{' '}
                    <span className={c.pnl! >= 0 ? 'text-buy' : 'text-sell'}>{c.pnl! >= 0 ? '+' : ''}{c.pnl} $</span>
                  </p>
                ))}
              </div>
            )}
          </>
        ) : <p className="mt-2 text-sm text-muted">Chargement…</p>}
      </section>

      {/* 3. Les opportunités du jour (4h = timeframe validé) */}
      <section className="rounded-xl border border-border bg-surface p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">🎯 Les opportunités du jour (4h)</h2>
          <a href="/daily" className="text-xs text-accent hover:underline">tout voir →</a>
        </div>
        {picksLocked && <p className="mt-2 text-sm text-muted">Réservé au plan Pro+. <a href="/plans" className="text-accent underline">Mettre à niveau</a></p>}
        {picks && picks.length === 0 && <p className="mt-2 text-sm text-muted">Rien de convaincant aujourd&apos;hui — s&apos;abstenir est une décision valable.</p>}
        {picks && picks.length > 0 && (
          <div className="mt-2 grid gap-2 md:grid-cols-3">
            {picks.map((p) => (
              <div key={p.symbol} className={`rounded-lg border p-3 ${p.tier === 'confirmed' ? 'border-buy/40' : 'border-yellow-500/30'}`}>
                <div className="flex items-center justify-between text-sm">
                  <span className="font-mono font-semibold text-white">{p.symbol}</span>
                  <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${p.direction === 'BUY' ? 'bg-buy/20 text-buy' : 'bg-sell/20 text-sell'}`}>{p.direction}</span>
                </div>
                <p className="mt-1 text-[10px] text-muted">{p.tier === 'confirmed' ? '★ confirmé par backtest' : '👀 à surveiller'}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* 4. Track record réel + ce que les filtres t'ont évité */}
      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-2 text-sm font-semibold text-white">📈 Mes prédictions — issues réelles</h2>
          {obs && obs.closed > 0 ? (
            <>
              <p className="text-2xl font-bold text-white">{obs.win_rate}% <span className="text-sm font-normal text-muted">de réussite</span></p>
              <p className="mt-1 text-xs text-muted">{obs.wins} gagnées · {obs.losses} perdues · {obs.open} en cours — issues vérifiées sur le prix réel, y compris les perdantes.</p>
            </>
          ) : (
            <p className="text-sm text-muted">Pas encore de trade résolu. Génère des signaux : leurs issues s&apos;afficheront ici, gagnées comme perdues.</p>
          )}
        </div>
        <div className="rounded-xl border border-accent/30 bg-accent/5 p-4">
          <h2 className="mb-2 text-sm font-semibold text-white">🛡️ Ce que les filtres t&apos;ont évité</h2>
          {av && av.blocked > 0 ? (
            <>
              <p className="text-2xl font-bold text-white">{av.would_have_lost} <span className="text-sm font-normal text-muted">trade(s) perdant(s) évité(s)</span></p>
              <p className="mt-1 text-xs text-muted">
                Sur {av.blocked} signaux bloqués (multi-timeframe, qualité, news) : {av.would_have_lost} auraient perdu,{' '}
                {av.would_have_won} auraient gagné{av.undecided ? `, ${av.undecided} indécis` : ''} — on te montre les deux, honnêtement.
              </p>
            </>
          ) : (
            <p className="text-sm text-muted">Aucun signal bloqué récemment. Quand un gate refusera un trade, tu verras ici s&apos;il t&apos;a protégé.</p>
          )}
        </div>
      </section>

      <p className="text-[11px] text-muted">
        Aide à la décision, pas un conseil en investissement. Les performances passées ne préjugent pas des résultats futurs.
      </p>
    </div>
  );
}

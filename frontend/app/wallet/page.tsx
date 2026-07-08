'use client';

import { useEffect, useState } from 'react';
import { api, Wallet } from '@/lib/api';

export default function WalletPage() {
  const [w, setW] = useState<Wallet | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startBal, setStartBal] = useState('10000');

  async function load() {
    setLoading(true);
    try {
      setW(await api.wallet());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
    const id = setInterval(load, 30000); // suit les clôtures auto
    return () => clearInterval(id);
  }, []);

  async function reset() {
    if (!confirm('Réinitialiser le portefeuille et effacer l’historique des trades papier ?')) return;
    setW(await api.resetWallet(parseFloat(startBal) || 10000, true));
  }

  if (loading && !w) return <div className="p-8 text-white">Chargement…</div>;
  if (error) return <div className="p-8 text-sell">{error}</div>;
  if (!w) return null;

  const st = w.stats;
  const pnlColor = (v: number) => (v >= 0 ? 'text-buy' : 'text-sell');
  // Mini courbe d'équité (SVG simple).
  const pts = [{ equity: w.starting_balance }, ...w.equity_curve];
  const eqs = pts.map((p) => p.equity);
  const min = Math.min(...eqs), max = Math.max(...eqs), span = max - min || 1;
  const path = pts.map((p, i) => `${(i / Math.max(1, pts.length - 1)) * 100},${30 - ((p.equity - min) / span) * 28}`).join(' ');

  return (
    <div className="p-8 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Portefeuille virtuel</h1>
          <p className="text-sm text-muted">Compte simulé : ton solde évolue exactement comme un vrai compte, au fil de tes trades papier.</p>
        </div>
        <a href="/execution" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">Paper Trading →</a>
      </header>

      {/* Solde & équité */}
      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Big label="Solde" value={`${w.balance.toLocaleString()} $`} sub={`départ ${w.starting_balance.toLocaleString()} $`} />
        <Big label="Équité (avec positions ouvertes)" value={`${w.equity.toLocaleString()} $`} />
        <Big label="P&L réalisé" value={`${w.realized_pnl >= 0 ? '+' : ''}${w.realized_pnl.toLocaleString()} $`} color={pnlColor(w.realized_pnl)} />
        <Big label="Performance" value={`${w.return_pct >= 0 ? '+' : ''}${w.return_pct}%`} color={pnlColor(w.return_pct)} sub={`latent ${w.unrealized_pnl >= 0 ? '+' : ''}${w.unrealized_pnl} $`} />
      </section>

      {/* Courbe d'équité */}
      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="mb-2 text-sm font-semibold text-white">Courbe d’équité ({st.trades} trade(s) clôturé(s))</h2>
        {w.equity_curve.length > 0 ? (
          <svg viewBox="0 0 100 30" preserveAspectRatio="none" className="h-24 w-full">
            <polyline points={path} fill="none" stroke={w.return_pct >= 0 ? '#1D9E75' : '#E24B4A'} strokeWidth="0.6" />
          </svg>
        ) : (
          <p className="text-sm text-muted">Aucun trade clôturé. Passe des ordres en <a href="/execution" className="text-accent underline">Paper Trading</a> et laisse-les se résoudre.</p>
        )}
      </section>

      {/* Statistiques de fiabilité */}
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Taux de réussite" value={`${st.win_rate}%`} color={st.win_rate >= 50 ? 'text-buy' : 'text-sell'} />
        <Stat label="Profit factor" value={st.profit_factor} color={st.profit_factor >= 1 ? 'text-buy' : 'text-sell'} />
        <Stat label="Gagnants / Perdants" value={`${st.wins} / ${st.losses}`} />
        <Stat label="Positions ouvertes" value={st.open_positions} />
        <Stat label="Meilleur trade" value={`${st.best_trade >= 0 ? '+' : ''}${st.best_trade} $`} color="text-buy" />
        <Stat label="Pire trade" value={`${st.worst_trade} $`} color="text-sell" />
      </section>

      {/* Positions ouvertes */}
      {w.positions.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-lg font-semibold text-white">Positions ouvertes ({w.positions.length})</h2>
          {w.positions.map((p) => (
            <div key={p.id} className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-surface p-3 text-sm">
              <span className="font-mono text-white">{p.symbol}</span>
              <span className={p.side === 'buy' ? 'text-buy' : 'text-sell'}>{p.side}</span>
              <span className="text-muted">{p.qty} @ {p.entry}</span>
              <span className="text-muted">prix {p.current_price ?? '—'}</span>
              <span className={`ml-auto ${pnlColor(p.unrealized_pnl)}`}>P&L latent {p.unrealized_pnl >= 0 ? '+' : ''}{p.unrealized_pnl} $</span>
            </div>
          ))}
        </section>
      )}

      {/* Réinitialisation */}
      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="mb-2 text-sm font-semibold text-white">Recommencer à zéro</h2>
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted">Solde de départ :</span>
          <input value={startBal} onChange={(e) => setStartBal(e.target.value)} inputMode="decimal"
            className="w-28 rounded border border-border bg-background px-2 py-1 font-mono text-white" />
          <span className="text-muted">$</span>
          <button onClick={reset} className="rounded-lg border border-sell/50 px-3 py-1 text-sm text-sell hover:bg-sell/10">
            Réinitialiser (efface l’historique)
          </button>
        </div>
      </section>

      <p className="text-xs text-muted">
        C’est le juge de paix : après plusieurs dizaines de trades, ce solde te dit objectivement si ta façon de trader est fiable.
        Argent fictif — aide à la décision, pas un conseil en investissement.
      </p>
    </div>
  );
}

function Big({ label, value, sub, color = 'text-white' }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${color}`}>{value}</p>
      {sub && <p className="text-[11px] text-muted">{sub}</p>}
    </div>
  );
}

function Stat({ label, value, color = 'text-white' }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-3">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-0.5 text-lg ${color}`}>{value}</p>
    </div>
  );
}

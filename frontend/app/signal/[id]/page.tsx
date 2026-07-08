'use client';

/**
 * Page PRÉDICTION DÉTAILLÉE — le « pourquoi » complet d'un BUY/SELL/HOLD.
 * Le trader consulte : la décision du Master, le vote de chaque agent (score + justification),
 * les gates (multi-timeframe, qualité, événementiel), les indicateurs, les news analysées,
 * les niveaux de trade et les scores de contexte/timing. Transparence totale.
 */
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { api, Signal } from '@/lib/api';

const AGENT_LABEL: Record<string, string> = {
  technical: 'Analyse technique', volume: 'Volume', sentiment: 'Sentiment & news',
  pattern: 'Figures chartistes', fundamental: 'Fondamentaux', macro: 'Macro-économie', risk: 'Risque',
};

export default function SignalDetailPage() {
  const params = useParams<{ id: string }>();
  const [s, setS] = useState<Signal | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (params?.id) api.getSignal(params.id).then(setS).catch((e) => setError(e.message));
  }, [params?.id]);

  if (error) return <div className="p-8 text-sell">{error}</div>;
  if (!s) return <div className="p-8 text-white">Chargement de la prédiction…</div>;

  const isBuy = s.direction === 'BUY';
  const isSell = s.direction === 'SELL';
  const badge = isBuy ? 'bg-buy/20 text-buy' : isSell ? 'bg-sell/20 text-sell' : 'bg-border text-muted';
  const m = s.metrics ?? {};
  // La 1re ligne du rationale = l'arbitrage du Master ; les puces = le détail des agents.
  const masterLine = (s.rationale || '').split('\n')[0];
  const gateLines = (s.rationale || '').split('\n').filter((l) => l.startsWith('⏸️'));

  return (
    <div className="mx-auto max-w-4xl space-y-5 p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="font-mono text-2xl font-bold text-white">{s.asset}</h1>
            <span className="rounded bg-surface px-2 py-0.5 text-xs text-muted">⏱ {s.timeframe}</span>
            <span className={`rounded-md px-3 py-1 text-sm font-bold ${badge}`}>{s.direction}</span>
            {s.high_conviction && <span className="rounded bg-buy/20 px-2 py-1 text-[10px] font-bold text-buy">★ HAUTE CONVICTION</span>}
          </div>
          <p className="mt-1 text-xs text-muted">
            Prédiction du {s.created_at ? new Date(s.created_at).toLocaleString('fr-FR') : '—'} · confiance {s.confidence}%
            {s.consensus_pct ? ` · consensus des agents ${s.consensus_pct}%` : ''}
          </p>
        </div>
        <a href="/dashboard" className="rounded-lg border border-border px-3 py-1 text-sm hover:bg-surface">← Dashboard</a>
      </header>

      {/* Issue RÉELLE de la prédiction — le track record vérifiable, prédiction par prédiction */}
      {s.trade_outcome && (
        <section className={`rounded-xl border p-3 text-sm ${
          s.trade_outcome.outcome === 'win' ? 'border-buy/50 bg-buy/10 text-buy'
          : s.trade_outcome.outcome === 'loss' ? 'border-sell/50 bg-sell/10 text-sell'
          : 'border-border bg-surface text-muted'}`}>
          {s.trade_outcome.outcome === 'win' && <>✅ <b>Cette prédiction a GAGNÉ</b>{s.trade_outcome.pnl != null ? ` (P&L ${s.trade_outcome.pnl >= 0 ? '+' : ''}${s.trade_outcome.pnl})` : ''} — issue vérifiée sur le prix réel.</>}
          {s.trade_outcome.outcome === 'loss' && <>🔴 <b>Cette prédiction a PERDU</b>{s.trade_outcome.pnl != null ? ` (P&L ${s.trade_outcome.pnl})` : ''} — on l&apos;affiche aussi : transparence totale.</>}
          {s.trade_outcome.outcome === 'open' && <>⏳ Prédiction <b>en cours</b> — l&apos;issue sera affichée ici dès que le prix touche le stop ou l&apos;objectif.</>}
        </section>
      )}

      {/* Pourquoi cette décision — l'arbitrage du Master + gates appliqués */}
      <section className="rounded-xl border border-accent/30 bg-accent/5 p-4">
        <h2 className="mb-1 text-sm font-semibold text-white">🧠 Pourquoi {s.direction} ?</h2>
        <p className="text-sm text-gray-200">{masterLine}</p>
        {gateLines.map((g, i) => (
          <p key={i} className="mt-1 rounded bg-yellow-500/10 px-2 py-1 text-xs text-yellow-200">{g}</p>
        ))}
        <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted">
          {m.context_score != null && <span>Score de contexte : <b className="text-white">{m.context_score}/100</b></span>}
          {m.timing_score != null && <span>Score de timing : <b className="text-white">{m.timing_score}/100</b></span>}
        </div>
      </section>

      {/* La PESÉE exacte de la décision : poids × score = contribution de chaque agent */}
      {m.master_decision && s.agents && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-1 text-sm font-semibold text-white">⚖️ Comment la décision a été pesée (les chiffres exacts)</h2>
          <p className="mb-3 text-xs text-muted">
            Score combiné : <b className="text-white">{m.master_decision.score >= 0 ? '+' : ''}{m.master_decision.score}</b>
            {' '}· seuil : BUY si &gt; +{m.master_decision.threshold} / SELL si &lt; −{m.master_decision.threshold}
            {' '}· consensus {m.master_decision.consensus}%{m.master_decision.conflict ? ' · ⚠️ agents en conflit (pondération prudente)' : ''}
          </p>
          <div className="space-y-1.5">
            {s.agents.filter((a) => a.name !== 'risk').map((a) => {
              const w = (m.master_decision.weights_used ?? {})[a.name] ?? 0;
              const contrib = w * a.score;
              const pct = Math.min(100, Math.abs(contrib) * 300);
              return (
                <div key={a.name} className="flex items-center gap-2 text-xs">
                  <span className="w-24 capitalize text-gray-300">{a.name}</span>
                  <span className="w-16 text-muted" title="poids effectif (base × apprentissage × régime)">poids {w.toFixed(2)}</span>
                  <span className={`w-14 text-right ${a.score > 0.05 ? 'text-buy' : a.score < -0.05 ? 'text-sell' : 'text-muted'}`}>{a.score >= 0 ? '+' : ''}{a.score.toFixed(2)}</span>
                  <div className="h-2 flex-1 rounded bg-border/40">
                    <div className={`h-2 rounded ${contrib > 0 ? 'bg-buy' : contrib < 0 ? 'bg-sell' : 'bg-border'}`} style={{ width: `${pct}%` }} />
                  </div>
                  <span className={`w-16 text-right font-mono ${contrib > 0 ? 'text-buy' : contrib < 0 ? 'text-sell' : 'text-muted'}`}>{contrib >= 0 ? '+' : ''}{contrib.toFixed(3)}</span>
                </div>
              );
            })}
          </div>
          <p className="mt-2 text-[10px] text-muted">Contribution = poids effectif × score de l&apos;agent. La somme pondérée donne le score combiné qui force la décision.</p>
        </section>
      )}

      {/* Le vote de chaque agent */}
      {s.agents && s.agents.length > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-3 text-sm font-semibold text-white">🗳️ Le vote des agents (transparence complète)</h2>
          <div className="space-y-3">
            {s.agents.map((a) => {
              const pct = Math.min(100, Math.abs(a.score) * 100);
              const tone = a.score > 0.05 ? 'bg-buy' : a.score < -0.05 ? 'bg-sell' : 'bg-border';
              const dir = a.score > 0.05 ? 'ACHAT' : a.score < -0.05 ? 'VENTE' : 'NEUTRE';
              return (
                <div key={a.name} className="rounded-lg border border-border/60 bg-background/50 p-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-white">{AGENT_LABEL[a.name] ?? a.name}</span>
                    <span className={a.score > 0.05 ? 'text-buy' : a.score < -0.05 ? 'text-sell' : 'text-muted'}>
                      {dir} {a.score >= 0 ? '+' : ''}{a.score.toFixed(2)} · confiance {(a.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="mt-1.5 h-1.5 w-full rounded bg-border/40">
                    <div className={`h-1.5 rounded ${tone}`} style={{ width: `${pct}%` }} />
                  </div>
                  <p className="mt-2 whitespace-pre-line text-xs text-gray-300">{a.rationale}</p>
                  {/* Données structurées de l'agent : les FAITS derrière la phrase */}
                  {a.details && Object.keys(a.details).length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {Array.isArray(a.details.patterns) && a.details.patterns.map((p: string) => (
                        <span key={p} className="rounded bg-accent/15 px-2 py-0.5 text-[10px] text-accent">🕯️ {p}</span>
                      ))}
                      {a.details.fear_greed != null && (
                        <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">Fear &amp; Greed : {a.details.fear_greed}/100</span>
                      )}
                      {a.details.news_count != null && (
                        <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">{a.details.news_count} news analysées</span>
                      )}
                      {a.details.funding_rate != null && (
                        <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">Funding {(a.details.funding_rate * 100).toFixed(3)}%</span>
                      )}
                      {a.details.btc_lead != null && (
                        <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">BTC lead {a.details.btc_lead >= 0 ? '+' : ''}{a.details.btc_lead}</span>
                      )}
                      {a.details.dxy != null && (
                        <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">DXY {a.details.dxy >= 0 ? '+' : ''}{a.details.dxy}</span>
                      )}
                      {a.details.spx_regime && (
                        <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">SPX : {a.details.spx_regime}</span>
                      )}
                      {a.details.gap_pct != null && (
                        <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">Gap {a.details.gap_pct}%</span>
                      )}
                      {a.details.penalty != null && a.details.penalty > 0 && (
                        <span className="rounded bg-sell/15 px-2 py-0.5 text-[10px] text-sell">Pénalité risque {a.details.penalty}</span>
                      )}
                      {a.details.ratios && <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">PER {a.details.ratios.pe ?? '—'} · marge {(a.details.ratios.net_margin != null ? (a.details.ratios.net_margin * 100).toFixed(0) + '%' : '—')}</span>}
                      {a.details.vision_used && <span className="rounded bg-background px-2 py-0.5 text-[10px] text-gray-300">🖼️ vision IA utilisée</span>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Multi-timeframe */}
      {s.mtf && s.mtf.total > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-2 text-sm font-semibold text-white">🕐 Confirmation multi-timeframe ({s.mtf.aligned}/{s.mtf.total} alignés)</h2>
          <div className="flex flex-wrap gap-2 text-xs">
            {Object.entries(s.mtf.details).map(([tf, dir]) => (
              <span key={tf} className={`rounded px-2 py-1 ${dir === 'BUY' ? 'bg-buy/15 text-buy' : dir === 'SELL' ? 'bg-sell/15 text-sell' : 'bg-border text-muted'}`}>
                {tf} → {dir}
              </span>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-muted">Un signal directionnel n&apos;est émis que si ≥2/3 unités de temps s&apos;accordent — sinon HOLD.</p>
        </section>
      )}

      {/* Niveaux de trade */}
      {s.direction !== 'HOLD' && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-2 text-sm font-semibold text-white">🎯 Plan de trade proposé</h2>
          <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
            <div><p className="text-xs text-muted">Entrée</p><p className="font-mono text-white">{s.entry}</p></div>
            <div><p className="text-xs text-muted">Stop-Loss</p><p className="font-mono text-sell">{s.stop_loss}</p></div>
            <div><p className="text-xs text-muted">Take-Profit 1</p><p className="font-mono text-buy">{s.take_profit_1}</p></div>
            <div><p className="text-xs text-muted">R/R</p><p className="font-mono text-white">1 : {s.risk_reward}</p></div>
          </div>
          {s.risk_warning && <p className="mt-2 rounded bg-yellow-500/10 px-2 py-1 text-xs text-yellow-200">{s.risk_warning}</p>}
        </section>
      )}

      {/* Indicateurs techniques */}
      {Object.keys(m).length > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-2 text-sm font-semibold text-white">📊 Indicateurs au moment de la prédiction</h2>
          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs sm:grid-cols-3">
            {m.trend && <Row k="Tendance" v={m.trend} />}
            {m.rsi != null && <Row k="RSI(14)" v={`${m.rsi} (${m.rsi_state ?? ''})`} />}
            {m.macd && <Row k="MACD" v={m.macd.state} />}
            {m.adx != null && <Row k="ADX" v={`${m.adx} (${m.adx_state ?? ''})`} />}
            {m.stochastic && <Row k="Stochastique %K" v={`${m.stochastic.k} (${m.stochastic.state})`} />}
            {m.ema20 != null && <Row k="EMA 20 / 50" v={`${m.ema20} / ${m.ema50}`} />}
            {m.bollinger && <Row k="Bollinger" v={m.bollinger.position} />}
            {m.atr_pct != null && <Row k="Volatilité (ATR)" v={`${m.atr_pct}%`} />}
            {m.vs_vwap && <Row k="VWAP" v={m.vs_vwap} />}
            {m.obv_trend && <Row k="OBV" v={m.obv_trend} />}
            {m.support != null && <Row k="Support" v={m.support} />}
            {m.resistance != null && <Row k="Résistance" v={m.resistance} />}
            {m.funding_rate != null && <Row k="Funding rate" v={`${(m.funding_rate * 100).toFixed(3)}%`} />}
            {m.spx_regime && <Row k="Régime SPX" v={m.spx_regime} />}
            {m.pos_52 != null && <Row k="Position 52 périodes" v={`${m.pos_52}%`} />}
          </div>

          {/* Niveaux pro : points pivots + Fibonacci (ce que les institutionnels surveillent) */}
          {(m.pivots || m.fibonacci) && (
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {m.pivots && (
                <div className="rounded-lg border border-border/60 bg-background/50 p-3">
                  <p className="mb-1 text-xs font-semibold text-white">Points pivots (classiques)</p>
                  <div className="grid grid-cols-2 gap-x-4 text-xs">
                    <Row k="R2" v={m.pivots.r2} /><Row k="R1" v={m.pivots.r1} />
                    <Row k="Pivot" v={m.pivots.p} /><Row k="S1" v={m.pivots.s1} />
                    <Row k="S2" v={m.pivots.s2} />
                  </div>
                </div>
              )}
              {m.fibonacci && (
                <div className="rounded-lg border border-border/60 bg-background/50 p-3">
                  <p className="mb-1 text-xs font-semibold text-white">Fibonacci — swing {m.fibonacci.swing}</p>
                  <div className="grid grid-cols-2 gap-x-4 text-xs">
                    <Row k="Haut" v={m.fibonacci.high} /><Row k="38.2%" v={m.fibonacci.levels?.['38.2']} />
                    <Row k="50%" v={m.fibonacci.levels?.['50']} /><Row k="61.8%" v={m.fibonacci.levels?.['61.8']} />
                    <Row k="Bas" v={m.fibonacci.low} />
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* News analysées */}
      {s.news && s.news.length > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="mb-2 text-sm font-semibold text-white">📰 News analysées par l&apos;agent sentiment</h2>
          <ul className="space-y-1.5">
            {s.news.map((n, i) => (
              <li key={i} className="flex items-start gap-2 text-xs">
                <span className={n.sentiment != null && n.sentiment > 0.05 ? 'text-buy' : n.sentiment != null && n.sentiment < -0.05 ? 'text-sell' : 'text-muted'}>
                  {n.sentiment != null && n.sentiment > 0.05 ? '▲' : n.sentiment != null && n.sentiment < -0.05 ? '▼' : '•'}
                </span>
                <span className="flex-1 text-gray-300">{n.headline}</span>
                {n.sentiment != null && (
                  <span className={`shrink-0 font-mono ${n.sentiment > 0.05 ? 'text-buy' : n.sentiment < -0.05 ? 'text-sell' : 'text-muted'}`}>
                    {n.sentiment >= 0 ? '+' : ''}{Number(n.sentiment).toFixed(2)}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-[11px] text-muted">
        Prédiction générée automatiquement par l&apos;analyse multi-agents. Aide à la décision, pas un conseil
        en investissement — vérifie toujours par toi-même avant d&apos;agir.
      </p>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string | number }) {
  return (
    <div className="flex justify-between gap-2 border-b border-border/30 py-0.5">
      <span className="text-muted">{k}</span>
      <span className="font-mono text-white">{v}</span>
    </div>
  );
}

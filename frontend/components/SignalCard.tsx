/**
 * Signal Card — composant central de l'UI (cf. cahier des charges §5.3).
 * Affiche les niveaux, la confiance, le tableau de bord des indicateurs et le détail par agent.
 */
import type { Signal } from '@/lib/api';

export function SignalCard({ s }: { s: Signal }) {
  const isBuy = s.direction === 'BUY';
  const isSell = s.direction === 'SELL';
  const badge = isBuy ? 'bg-buy-soft text-buy' : isSell ? 'bg-sell-soft text-sell' : 'bg-border text-muted';
  const tps = [s.take_profit_1, s.take_profit_2, s.take_profit_3].filter((t) => t != null) as number[];
  const m = s.metrics ?? {};

  return (
    <div className="w-full max-w-lg rounded-xl border border-border bg-surface p-5 shadow-lg">
      <div className="flex items-center justify-between">
        <span className="font-mono text-lg font-semibold">{s.asset}</span>
        <span className={`rounded-md px-3 py-1 text-sm font-bold ${badge}`}>{s.direction}</span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <Field label="Entrée" value={s.entry} />
        <Field label="Stop-Loss" value={s.stop_loss} className="text-sell" />
        {tps[0] != null && <Field label="TP 1" value={tps[0]} className="text-buy" />}
        {tps[1] != null && <Field label="TP 2" value={tps[1]} className="text-buy" />}
        {tps[2] != null && <Field label="TP 3" value={tps[2]} className="text-buy" />}
        <Field label="R/R" value={`1 : ${s.risk_reward}`} />
      </div>

      <div className="mt-4">
        <div className="mb-1 flex justify-between text-xs text-muted">
          <span>Score de confiance{s.consensus_pct ? ` · consensus ${s.consensus_pct}%` : ''}</span>
          <span className={s.confidence >= 70 ? 'text-buy' : s.confidence >= 45 ? 'text-white' : 'text-muted'}>{s.confidence}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-border">
          <div className={`h-2 rounded-full ${s.confidence >= 70 ? 'bg-buy' : 'bg-accent'}`} style={{ width: `${s.confidence}%` }} />
        </div>
      </div>

      {Object.keys(m).length > 0 && (
        <div className="mt-4">
          <p className="mb-2 text-xs font-semibold text-white">Indicateurs techniques</p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-3">
            {m.trend && <Metric label="Tendance" value={m.trend} />}
            {m.rsi != null && <Metric label="RSI(14)" value={`${m.rsi} (${m.rsi_state ?? ''})`} tone={m.rsi < 30 ? 'buy' : m.rsi > 70 ? 'sell' : ''} />}
            {m.macd && <Metric label="MACD" value={m.macd.state} tone={m.macd.state === 'haussier' ? 'buy' : 'sell'} />}
            {m.adx != null && <Metric label="ADX" value={`${m.adx} (${m.adx_state ?? ''})`} />}
            {m.stochastic && <Metric label="Stoch %K" value={`${m.stochastic.k} (${m.stochastic.state})`} />}
            {m.ema20 != null && <Metric label="EMA20/50" value={`${m.ema20} / ${m.ema50}`} />}
            {m.bollinger && <Metric label="Bollinger" value={m.bollinger.position} />}
            {m.atr_pct != null && <Metric label="Volatilité (ATR)" value={`${m.atr_pct}%`} />}
            {m.vs_vwap && <Metric label="VWAP" value={m.vs_vwap} />}
            {m.obv_trend && <Metric label="OBV" value={m.obv_trend} />}
            {m.support != null && <Metric label="Support" value={m.support} tone="buy" />}
            {m.resistance != null && <Metric label="Résistance" value={m.resistance} tone="sell" />}
          </div>
        </div>
      )}

      <details className="mt-4 group">
        <summary className="cursor-pointer text-xs font-semibold text-white">Analyse détaillée (agents)</summary>
        <p className="mt-2 whitespace-pre-line text-xs text-muted">{s.rationale}</p>
        {s.agents && s.agents.length > 0 && (
          <div className="mt-2 space-y-1">
            {s.agents.map((a) => (
              <div key={a.name} className="flex items-center gap-2 text-[11px]">
                <span className="w-20 shrink-0 capitalize text-gray-400">{a.name}</span>
                <span className={a.score > 0.1 ? 'text-buy' : a.score < -0.1 ? 'text-sell' : 'text-muted'}>{a.score >= 0 ? '+' : ''}{a.score.toFixed(2)}</span>
              </div>
            ))}
          </div>
        )}
      </details>

      <p className="mt-3 text-[10px] text-muted">Timeframe : {s.timeframe} · Aide à la décision, pas un conseil en investissement.</p>
    </div>
  );
}

function Field({ label, value, className = '' }: { label: string; value: string | number; className?: string }) {
  return (
    <div>
      <div className="text-xs text-muted">{label}</div>
      <div className={`font-mono ${className}`}>{value}</div>
    </div>
  );
}

function Metric({ label, value, tone = '' }: { label: string; value: string | number; tone?: string }) {
  const color = tone === 'buy' ? 'text-buy' : tone === 'sell' ? 'text-sell' : 'text-white';
  return (
    <div className="flex justify-between gap-2 border-b border-border/40 py-0.5">
      <span className="text-muted">{label}</span>
      <span className={`font-mono ${color}`}>{value}</span>
    </div>
  );
}

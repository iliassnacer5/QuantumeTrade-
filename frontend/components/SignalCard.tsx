/**
 * Signal Card — composant central de l'UI (cf. cahier des charges §5.3).
 * Version statique de démonstration pour la Phase 0 ; branchée sur l'API en Phase 1.
 */
export type Signal = {
  asset: string;
  direction: 'BUY' | 'SELL' | 'HOLD';
  entry: number;
  stopLoss: number;
  takeProfit: [number, number, number];
  riskReward: number;
  confidence: number;
  timeframe: string;
  rationale: string;
};

export function SignalCard({ s }: { s: Signal }) {
  const isBuy = s.direction === 'BUY';
  const badge = isBuy ? 'bg-buy-soft text-buy' : 'bg-sell-soft text-sell';

  return (
    <div className="w-full max-w-md rounded-xl border border-border bg-surface p-5 shadow-lg">
      <div className="flex items-center justify-between">
        <span className="font-mono text-lg font-semibold">{s.asset}</span>
        <span className={`rounded-md px-3 py-1 text-sm font-bold ${badge}`}>{s.direction}</span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <Field label="Entrée" value={s.entry} />
        <Field label="Stop-Loss" value={s.stopLoss} className="text-sell" />
        <Field label="TP 1" value={s.takeProfit[0]} className="text-buy" />
        <Field label="TP 2" value={s.takeProfit[1]} className="text-buy" />
        <Field label="TP 3" value={s.takeProfit[2]} className="text-buy" />
        <Field label="R/R" value={`1 : ${s.riskReward}`} />
      </div>

      <div className="mt-4">
        <div className="mb-1 flex justify-between text-xs text-muted">
          <span>Score de confiance</span>
          <span>{s.confidence}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-border">
          <div className="h-2 rounded-full bg-accent" style={{ width: `${s.confidence}%` }} />
        </div>
      </div>

      <p className="mt-4 text-xs text-muted">
        <span className="font-semibold text-white">Justification IA :</span> {s.rationale}
      </p>
      <p className="mt-2 text-[10px] text-muted">Timeframe : {s.timeframe}</p>
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

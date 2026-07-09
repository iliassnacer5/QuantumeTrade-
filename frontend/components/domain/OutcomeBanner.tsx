import { cn } from '@/lib/cn';

export type Outcome = 'won' | 'lost' | 'open' | 'win' | 'loss' | 'breakeven' | string;

const STYLE: Record<string, { tone: string; label: string }> = {
  won: { tone: 'border-buy/40 bg-buy/10 text-buy', label: '✅ Gagné' },
  win: { tone: 'border-buy/40 bg-buy/10 text-buy', label: '✅ Gagné' },
  lost: { tone: 'border-sell/40 bg-sell/10 text-sell', label: '❌ Perdu' },
  loss: { tone: 'border-sell/40 bg-sell/10 text-sell', label: '❌ Perdu' },
  breakeven: { tone: 'border-border bg-surface text-muted', label: '➖ Neutre' },
  open: { tone: 'border-accent/40 bg-accent/10 text-accent', label: '⏳ En cours' },
};

/** Bannière/pastille d'issue de trade (gagné / perdu / en cours). */
export function OutcomeBanner({
  outcome,
  pnl,
  className,
}: {
  outcome: Outcome;
  pnl?: number | null;
  className?: string;
}) {
  const s = STYLE[outcome] ?? STYLE.open;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium',
        s.tone,
        className,
      )}
    >
      {s.label}
      {pnl != null && (
        <span className="font-mono">
          {pnl >= 0 ? '+' : ''}
          {pnl}
        </span>
      )}
    </span>
  );
}

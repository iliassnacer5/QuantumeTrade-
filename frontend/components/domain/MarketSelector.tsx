'use client';

import { MARKET_CLASSES } from '@/lib/markets';
import { cn } from '@/lib/cn';

/** Sélecteur de marché partagé (Tous/Crypto/Forex/Actions/Or). Remplace 5 copies inline. */
export function MarketSelector({
  value,
  onChange,
  includeAll = true,
  label = 'Marché',
  className,
}: {
  value: string;
  onChange: (id: string) => void;
  includeAll?: boolean;
  label?: string | null;
  className?: string;
}) {
  const classes = includeAll ? MARKET_CLASSES : MARKET_CLASSES.filter((c) => c.id);
  return (
    <div className={cn('flex flex-wrap items-center gap-1.5', className)}>
      {label && <span className="mr-1 text-xs text-muted">{label} :</span>}
      {classes.map((c) => (
        <button
          key={c.id}
          onClick={() => onChange(c.id)}
          className={cn(
            'rounded-lg border px-2.5 py-1 text-xs transition',
            value === c.id
              ? 'border-accent bg-accent/10 text-white'
              : 'border-border text-muted hover:bg-surface',
          )}
        >
          {c.label}
        </button>
      ))}
    </div>
  );
}

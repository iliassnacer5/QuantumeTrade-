'use client';

import { cn } from '@/lib/cn';

export type SymbolItem = { symbol: string; asset_class?: string; label?: string };

/**
 * Catalogue de symboles cliquables (grille compacte scrollable).
 * Le parent fournit la liste (filtrée par marché/session) et l'actif sélectionné.
 */
export function SymbolPicker({
  symbols,
  value,
  onChange,
  className,
  empty = 'Aucun symbole.',
}: {
  symbols: SymbolItem[];
  value: string;
  onChange: (symbol: string) => void;
  className?: string;
  empty?: string;
}) {
  return (
    <div className={cn('flex max-h-28 flex-wrap gap-1.5 overflow-y-auto', className)}>
      {symbols.map((s) => (
        <button
          key={s.symbol}
          onClick={() => onChange(s.symbol)}
          className={cn(
            'rounded px-2 py-1 font-mono text-[11px] transition',
            value === s.symbol
              ? 'bg-accent text-background'
              : 'bg-background text-muted hover:bg-border hover:text-white',
          )}
        >
          {s.symbol}
        </button>
      ))}
      {symbols.length === 0 && <span className="text-xs text-muted">{empty}</span>}
    </div>
  );
}

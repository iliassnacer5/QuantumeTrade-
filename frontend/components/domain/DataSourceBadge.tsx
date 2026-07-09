import { cn } from '@/lib/cn';

/**
 * Indique la provenance des données : réelles (live/marché) vs démo (simulées).
 * Accepte soit un booléen `real`, soit un libellé explicite.
 */
export function DataSourceBadge({
  real,
  label,
  className,
}: {
  real: boolean;
  label?: string;
  className?: string;
}) {
  const text = label ?? (real ? 'Données réelles' : 'Démo');
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-2xs font-medium',
        real ? 'border-buy/40 bg-buy-soft text-buy' : 'border-warn/40 bg-warn-soft text-warn',
        className,
      )}
      title={real ? 'Basé sur des données de marché réelles' : 'Données simulées (démo) — non exploitables telles quelles'}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', real ? 'bg-buy' : 'bg-warn')} />
      {text}
    </span>
  );
}

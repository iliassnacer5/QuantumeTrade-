import { cn } from '@/lib/cn';

export type EdgeStatus = 'green' | 'yellow' | 'red' | string;

const EMOJI: Record<string, string> = { green: '🟢', yellow: '🟡', red: '🔴' };
const LABEL: Record<string, string> = {
  green: 'exploitable',
  yellow: 'à surveiller',
  red: 'sans edge',
};

/** Pastille de statut d'edge (🟢🟡🔴). `withLabel` ajoute le libellé. */
export function EdgeStatusDot({
  status,
  withLabel = false,
  className,
}: {
  status: EdgeStatus;
  withLabel?: boolean;
  className?: string;
}) {
  return (
    <span className={cn('inline-flex items-center gap-1', className)}>
      <span>{EMOJI[status] ?? '⚪'}</span>
      {withLabel && <span className="text-xs text-muted">{LABEL[status] ?? status}</span>}
    </span>
  );
}
